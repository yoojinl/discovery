from pecan import abort, expose
from oslo_config import cfg


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


class RootController(object):

    @expose(generic=True, template='json')
    def index(self):
        return parse_dnsmasq_leases(CONF.dnsmasq_leases)
