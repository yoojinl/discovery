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

from discovery import models


class DiskController(rest.RestController):

    @pecan.expose(template='json')
    def get_all(self, node_mac):
        node_mac = node_mac.lower()
        try:
            return models.NODES[node_mac]['discovery']['block_device']
        except KeyError:
            pecan.abort(404, 'Node or disk info not found')
