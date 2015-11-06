# -*- coding: utf-8 -*-

#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See then
#    License for the specific language governing permissions and limitations
#    under the License.

import 
from oslo_config import cfg
from oslo_log import log
from oslo_service import periodic_task
from oslo_service import service
from oslo_service import threadgroup
from keystoneclient.v2_0 import client

from discovery.scanners.base import BaseScanner


LOG = log.getLogger(__name__)


class NailgunScanner(BaseScanner):

    name = 'nailgun_scanner'
    version = '1.0.0.dev'

    cli_opts = [
        cfg.StrOpt(
            'nailgun_nodes_endpoint',
            default='http://10.20.0.2:8000/api/v1/nodes/',
            help='Nailgun api endpoint'),
        # TODO in production these parameters should be
        # read from config, not to expose them in bash
        # history
        cfg.StrOpt(
            'nailgun_password',
            default='admin',
            help='Nailgun password'),
        cfg.StrOpt(
            'nailgun_user',
            default='admin',
            help='Nailgun user'),
        cfg.StrOpt(
            'nailgun_keystone_endpoint',
            default='http://0.0.0.0:8000/keystone/v2.0',
            help='Nailgun api endpoint'),
        cfg.StrOpt(
            'nailgun_keystone_tenant',
            default='admin',
            help='Keystone tenant for nailgun'),
        cfg.IntOpt(
            'nailgun_interval',
            default=5,
            help='Scanning interval')]

    def run(self):
        LOG.info('Starting scanner %s %s', self.name, self.version)
        keystone = client.Client(
             username=self.config.nailgun_user,
             password=self.config.nailgun_password,
             tenant_name=self.config.nailgun_keystone_tenant,
             auth_url=self.config.nailgun_keystone_endpoint)
        keystone.authenticate()

        class PeriodicTask(periodic_task.PeriodicTasks):
            @periodic_task.periodic_task(
                run_immediately=True,
                spacing=self.config.nailgun_interval)
            def run(_self, *args, **kwargs):
                self.on_tick(keystone)

        task = PeriodicTask(self.config)
        
        tg = threadgroup.ThreadGroup()
        tg.add_dynamic_timer(task.run, context=None)

        srv = service.Service()
        srv.tg.add_dynamic_timer(task.run, context=None)

        service_launcher = service.ServiceLauncher(self.config)
        service_launcher.launch_service(srv)
        service_launcher.wait()

    def on_tick(self, keystone):
        try:
            LOG.exception('Getting nodes from Nailgun %s', self.config.nailgun_nodes_endpoint)
            nodes = keystone.get(self.config.nailgun_nodes_endpoint)[1]

            for node in nodes:
                try:
                    node_id = self._match_node(node)

                    if node_id is None:
                        self.create_node(node)
                    else:
                        self.update_node(node_id, node)
                except Exception as exc:
                    LOG.exception(exc)
                    LOG.error("Failed to update the node %s", node)

        except Exception as exc:
            LOG.exception(exc)

    def _get_matching_data(self, data):
        return {'source_id': 'nailgun_{0}'.format(data['id'])}
