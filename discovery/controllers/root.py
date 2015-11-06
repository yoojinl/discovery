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
from copy import deepcopy

import six
import pecan

from pecan import rest
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


class MatchController(rest.RestController):

    @pecan.expose(template='json')
    def post(self):
        ids = []
        # TODO more complicated algorithm is required
        #
        # Basically here is the basic implementation of
        # OR condition.
        # We should be able to also implement AND condition
        # lets say we have two installation of Cobbler
        # they may have intersection in ids, so we should
        # be able to specify cobbler_id="rack1" AND id=2,
        # or cobbler_id="rack2" AND id=2, those should be
        # two differen nodes
        # Another case which should be covered is list overlappings,
        # as a user I may want to identify nodes uniqness by
        # interfaces mac addresses, so
        # [08:00:27:ea:2e:8d, 08:00:27:0d:fb:75] & [08:00:27:ea:2e:8d, 00:00:00:00:00:00]
        # is the same node.
        for node in pecan.request.json:
            matching = node['matching_data']
            for node_id, data in six.iteritems(models.NODES):
                for key, value in six.iteritems(matching):
                    if data['matching_data'].get(key) == value:
                        ids.append(node_id)
                        break

        return ids

    
class ActionsController(rest.RestController):

    match = MatchController()


class NodeController(rest.RestController):

    disks = disks.DiskController()
    actions = ActionsController()

    @pecan.expose(template='json')
    def get_one(self, node_id):
        node_id = node_id.lower()
        try:
            return models.NODES[node_id]
        except KeyError:
            pecan.abort(404, 'Node {0} do not exists'.format(node_id))

    @pecan.expose(template='json')
    def put(self, node_id):
        node_id = node_id.lower()
        if node_id not in models.NODES:
            pecan.abort(404, 'Node {0} do not exists'.format(node_id))
        node_data = pecan.request.json
        models.NODES[node_id]['matching_data'] = node_data.pop('matching_data')
        models.NODES[node_id]['discovery'] = node_data
        models.NODES[node_id]['id'] = node_id

        return models.NODES[node_id]

    @pecan.expose(template='json')
    def post(self):
        node_id = models.get_uuid()
        models.NODES[node_id] = {}
        node_data = pecan.request.json
        models.NODES[node_id]['matching_data'] = node_data.pop('matching_data')
        models.NODES[node_id]['discovery'] = node_data
        models.NODES[node_id]['id'] = node_id
        
        return models.NODES[node_id]


class RootController(object):

    nodes = NodeController()

    @pecan.expose(generic=True, template='json')
    def index(self):
        dnsmasq_nodes = parse_dnsmasq_leases(CONF.dnsmasq_leases)

        for node_data in dnsmasq_nodes:
            node_uuid = models.NODES_MAC_UUID_MAPPING.get(
                node_data['mac']) or models.get_uuid()

            if node_uuid not in models.NODES:
                models.NODES_MAC_UUID_MAPPING[node_data['mac']] = node_uuid

                new_node = deepcopy(models.EMPTY_NODE)
                new_node['id'] = node_uuid
                new_node.update(node_data)
                models.NODES[node_uuid] = new_node

        return models.NODES.values()
