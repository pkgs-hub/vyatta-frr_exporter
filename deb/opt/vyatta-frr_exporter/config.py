#!/usr/bin/env python3
import os

from sys import exit

from vyos.config import Config
from vyos.configdict import dict_merge
from vyos.configverify import verify_vrf
from vyos.util import call
from vyos.template import render
from vyos import ConfigError
from vyos import airbag
from jinja2 import Template


airbag.enable()

config_file = r'/etc/default/frr_exporter'

def get_config(config=None):
    if config:
        conf = config
    else:
        conf = Config()
    base = ['service', 'monitoring', 'frr-exporter']
    if not conf.exists(base):
        return None

    frr_exporter = conf.get_config_dict(base, get_first_key=True)

    return frr_exporter

def verify(frr_exporter):
    if frr_exporter is None:
        return None

    verify_vrf(frr_exporter)
    return None

def generate(frr_exporter):
    if frr_exporter is None:
        if os.path.isfile(config_file):
            os.unlink(config_file)
        return None

    with open('/opt/vyatta-frr_exporter/config.j2', 'r') as tmpl, open(config_file, 'w') as out:
        template = Template(tmpl.read()).render(data=frr_exporter)
        out.write(template)

    # Reload systemd manager configuration
    call('systemctl daemon-reload')

    return None

def apply(frr_exporter):
    if frr_exporter is None:
        # frr_exporter is removed in the commit
        call('systemctl stop frr_exporter.service')
        return None

    call('systemctl restart frr_exporter.service')
    return None

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        exit(1)
