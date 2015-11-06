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

from discovery.scanners.base import BaseScanner

import requests
import pyinotify

from oslo_config import cfg
from oslo_log import log
from oslo_serialization import jsonutils


LOG = log.getLogger(__name__)


class FileScanner(BaseScanner):

    name = 'file_scanner'
    version = '1.0.0.dev'
    cli_opts = [cfg.StrOpt('watch_file', help='File to be parsed')]

    watch_manager = pyinotify.WatchManager()
    mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE

    def run(self):
        LOG.info('Starting scanner %s %s', self.name, self.version)

        class EventHandler(pyinotify.ProcessEvent):
            def process_default(_self, event):
                self.on_file_update()

        handler = EventHandler()
        notifier = pyinotify.Notifier(self.watch_manager, handler)
        self.watch_manager.add_watch(self.config.watch_file, self.mask)
        notifier.loop()

    def on_file_update(self):
        try:
            LOG.exception('Starting parsing the file %s', self.config.watch_file)
            parsed_nodes = []
            with open(self.config.watch_file, 'r') as f:
                parsed_nodes = self._parse_file(f)

            for node in parsed_nodes:
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
            LOG.error("Couldn't parse file %s", self.config.watch_file)

    def _parse_file(self, file_name):
        """Parses nodes in the next format:
        [
          {
            "id": 1
            "disks": [
              ...
            ]
          }, ...
        ]
        """
        return jsonutils.load(file_name)

    def _get_matching_data(self, data):
        return {'id': data['id']}
