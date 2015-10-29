import json
import sys

from oslo_config import cfg
from oslo_log import log
from oslo_service import periodic_task
from oslo_service import service
from oslo_service import threadgroup

from fabric import api as fabric_api
import requests


LOG = log.getLogger()


DISCOVERY_SERVICE_OPTS = [
    cfg.IPOpt('discovery_host_ip',
              default='0.0.0.0',
              help='The IP address on which discovery-api listens.'),
    cfg.IntOpt('discovery_port',
               default=8881,
               min=1, max=65535,
               help='The TCP port on which discovry-api listens.'),
]

SCAN_OPTS = [
    cfg.IntOpt('scan_interval',
               default=60,
               help='Max interval size between scan tasks execution in '
                    'seconds.'),
    cfg.StrOpt('ssh_key',
               help='Path to SSH identity key file used to scan nodes',
               ),
    cfg.StrOpt('ssh_user',
               default='root',
               help='SSH user used to scan nodes',
               ),
]


def make_config():
    conf = cfg.ConfigOpts()
    log.register_options(conf)

    conf.register_opts(DISCOVERY_SERVICE_OPTS)
    conf.register_cli_opts(DISCOVERY_SERVICE_OPTS)

    conf.register_opts(SCAN_OPTS)
    conf.register_cli_opts(SCAN_OPTS)

    return conf


def parse_args(conf, args=None):
    project = 'discovery-scan'
    version = '1.0.0'

    conf(args=args if args else sys.argv[1:],
         project=project,
         version=version)
    log.setup(conf,
              project,
              version=version)


CONF = make_config()
parse_args(CONF)


class NodeDiscoveryService(periodic_task.PeriodicTasks):

    @periodic_task.periodic_task(run_immediately=True,
                                 spacing=CONF.scan_interval)
    def scan_nodes(self, *args, **kwargs):
        LOG.debug('Scaning nodes...')
        nodes = self._get_current_nodes()
        LOG.debug('Result of the scan: %s', nodes)

        for node in nodes:
            ohai_data = self._scan_node(node)
            self._feed_discovery(node, ohai_data)

    def _get_current_nodes(self):
        return self._api_request('GET', '/').json()

    def _feed_discovery(self, node, ohai_data):
        mac = node['mac']
        LOG.debug('Sending info for node %s', mac)
        return self._api_request(
            'PUT',
            '/nodes/{mac}/'.format(mac=mac),
            data=json.dumps(ohai_data),
        )

    def _api_request(self, method, endpoint, *args, **kwargs):
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]

        return requests.request(
            method,
            'http://{ip}:{port}/{endpoint}'.format(
                ip=self.conf.discovery_host_ip,
                port=self.conf.discovery_port,
                endpoint=endpoint,
            ),
            *args,
            **kwargs
        )

    def _scan_node(self, node):
        LOG.debug('Scanning node %s', node['mac'])
        with fabric_api.settings(
            host_string=node['ip'],
            user=self.conf.ssh_user,
            key_filename=self.conf.ssh_key,
            abort_on_prompts=True,
        ):
            output = fabric_api.run('ohai')
            return json.loads(output.stdout)


def main(conf=CONF):
    LOG.info('Starting...')

    ds = NodeDiscoveryService(conf)
    ds.add_periodic_task(ds.scan_nodes)

    tg = threadgroup.ThreadGroup()
    tg.add_dynamic_timer(
        ds.run_periodic_tasks,
        context=None,
    )

    srv = service.Service()
    srv.tg.add_dynamic_timer(
        ds.run_periodic_tasks,
        context=None,
    )

    service_launcher = service.ServiceLauncher(conf)
    service_launcher.launch_service(srv)
    service_launcher.wait()


if __name__ == '__main__':
    main()
