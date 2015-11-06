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

import sys
from wsgiref import simple_server

from oslo_config import cfg

from six.moves import socketserver
import pecan

CONF = cfg.CONF

API_SERVICE_OPTS = [
    cfg.StrOpt('host_ip',
               default='0.0.0.0',
               help='The IP address on which api listens.'),
    cfg.IntOpt('port',
               default=8881,
               min=1, max=65535,
               help='The TCP port on which api listens.'),
    cfg.StrOpt('dnsmasq_leases',
               default='/var/lib/misc/dnsmasq.leases',
               help='Path to dnsmasq leases.')]

opt_group = cfg.OptGroup(
    name='api',
    title='Options for the api service')

CONF.register_group(opt_group)
CONF.register_opts(API_SERVICE_OPTS, opt_group)
CONF.register_cli_opts(API_SERVICE_OPTS)


def start_app(host, port):
    app = pecan.make_app(
        'discovery.controllers.root.RootController',
        debug=True)

    wsgi = simple_server.make_server(host, port, app)
    wsgi.serve_forever()


def main():
    CONF(sys.argv[1:], project='discovery', version='1.0.0')

    host = CONF.host_ip
    port = CONF.port
    print('Start listening on {0}:{1}'.format(host, port))

    start_app(host, port)
