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
from oslo_config import cfg
from oslo_log import log

from discovery.scanners import BaseScanner


def configure():
    project = 'discovery-scanner'
    version = '1.0.0'

    CONF = cfg.CONF
    log.register_options(CONF)
    log.setup(CONF, project, version)

    cli_opts = [
        cfg.StrOpt('driver', help='Specify scanner driver', required=True),
        cfg.IPOpt('discovery_host_ip',
                  default='0.0.0.0',
                  help='The IP address on which discovery-api listens.'),
        cfg.IntOpt('discovery_port',
                   default=8881,
                   min=1, max=65535,
                   help='The TCP port on which discovry-api listens.')]

    CONF.register_cli_opts(cli_opts)
    available_scanners = BaseScanner.__subclasses__()
    # TODO add subcommands/groups not to load all parameters globally
    for scanner in available_scanners:
        CONF.register_cli_opts(scanner.cli_opts)
        
    CONF(sys.argv[1:], project=project, version=version)

    return CONF


def main():
    conf = configure()
    scanner_name = conf.driver
    scanner_class = None
    available_scanners = BaseScanner.__subclasses__()
    for s in available_scanners:
        if s.name == scanner_name:
            scanner_class = s

    if scanner_class is None:
        raise ValueError("Invalid scanner name %s, available scanners %s",
                         scanner_name, [s.name for s in available_scanners])

    scanner = scanner_class(conf)
    scanner.run()


if __name__ == '__main__':
    main()
