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
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import pecan
from pecan import rest
from copy import deepcopy

from oslo_config import cfg

from discovery.controllers import disks
from discovery import models


CONF = cfg.CONF


def parse_dnsmasq_leases(conf_path):
    try:
        with open(conf_path, 'r') as f:
            leases_raw = f.read()
    except Exception as exc:
        print("Error reading {0}".format(conf_path))
        print(exc)
        return []

    leases = map(lambda l: l.split(' '), leases_raw.split('\n'))

    result_leases = []
    used_ips = []
    # Latest ips in the file have higher priority
    for lease in reversed(leases):
        if lease[0]:
            mac = lease[1]
            ip = lease[2]
            if ip not in used_ips:
                result_leases.append({'mac': mac, 'ip': ip})
                used_ips.append(lease[2])

    return result_leases


class NodeController(rest.RestController):

    disks = disks.DiskController()

    @pecan.expose(template='json')
    def get_one(self, node_mac):
        node_mac = node_mac.lower()
        try:
            return models.NODES[node_mac]
        except KeyError:
            pecan.abort(404, 'Node {0} do not exists'.format(node_mac))

    @pecan.expose(template='json')
    def put(self, node_mac):
        node_mac = node_mac.lower()
        if node_mac not in models.NODES:
            pecan.abort(404, 'Node {0} do not exists'.format(node_mac))
        models.NODES[node_mac]['discovery'] = pecan.request.json
        return models.NODES[node_mac]


class RootController(object):

    nodes = NodeController()

    @pecan.expose(generic=True, template='json')
    def index(self):
        for node in parse_dnsmasq_leases(CONF.dnsmasq_leases):
            models.NODES.setdefault(node['mac'], deepcopy(models.EMPTY_NODE))
            models.NODES[node['mac']].update(node)

        return models.NODES.values()
