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

import requests

from oslo_log import log
from oslo_serialization import jsonutils

import abc
import six


LOG = log.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BaseScanner(object):

    cli_opts = []

    def __init__(self, config):
        self.config = config

    @abc.abstractproperty
    def name(self):
        """Uniq scanner name."""

    @abc.abstractproperty
    def version(self):
        """Version of scanner."""

    @abc.abstractmethod
    def run():
        """Define logic, how scanner should be started."""

    def _match_node(self, node):
        LOG.info('Start matching the node: %s', node)
        ids = self._discovery_request(
            'POST',
            '/nodes/actions/match',
            data=self._serialize_as_list_for_discovery(node))

        LOG.info('Response from the server:')
        LOG.info(ids.text)
        parsed_ids = ids.json()

        if parsed_ids:
            return parsed_ids[0]

        return None

    def update_node(self, node_id, data):
        LOG.info('Updating the node %s with data: %s', node_id, data)
        self._discovery_request(
            'PUT',
            'nodes/{0}'.format(node_id),
            data=self._serialize_for_discovery(data))

    def create_node(self, data):
        LOG.info('Creating the node with data: %s', data)
        self._discovery_request(
            'POST',
            'nodes',
            data=self._serialize_for_discovery(data))

    def _serialize_for_discovery(self, data):
        self._extend_with_matching(data)
        return jsonutils.dumps(data)

    def _serialize_as_list_for_discovery(self, data):
        self._extend_with_matching(data)
        return jsonutils.dumps([data])

    def _extend_with_matching(self, data):
        data.update({'matching_data': self._get_matching_data(data)})

    def _discovery_request(self, method, endpoint, *args, **kwargs):
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]

        return requests.request(
            method,
            'http://{ip}:{port}/{endpoint}'.format(
                ip=self.config.discovery_host_ip,
                port=self.config.discovery_port,
                endpoint=endpoint),
            *args,
            **kwargs)
