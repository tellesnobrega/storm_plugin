# Copyright (c) 2014 Hoang Do, Phuc Vo, P. Michiardi, D. Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo.config import cfg

from sahara import conductor as c
from sahara.openstack.common import log as logging


conductor = c.API
LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def get_config_value(service, name, cluster=None):
    if cluster:
        for ng in cluster.node_groups:
            if (ng.configuration().get(service) and
                    ng.configuration()[service].get(name)):
                return ng.configuration()[service][name]

    raise RuntimeError("Unable to get parameter '%s' from service %s",
                       name, service)


def generate_storm_config(master_hostname, zk_hostnames):

    cfg = {
        "nimbus.host": master_hostname,
        "worker.childopts": "-Xmx768m -Djava.net.preferIPv4Stack=true",
        "nimbus.childopts": "-Xmx1024m -Djava.net.preferIPv4Stack=true",
        "supervisor.childopts": "-Djava.net.preferIPv4Stack=true",
        "storm.zookeeper.servers": zk_hostnames,
        "ui.childopts": "-Xmx768m -Djava.net.preferIPv4Stack=true",
        "storm.local.dir": "/app/storm"
    }

    return cfg


def generete_slave_supervisor_conf(self):
    conf = "%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s" % (
           "[program:storm-supervisor]",
           'command=bash -exec "cd /usr/local/storm && bin/storm supervisor"',
           "user=storm",
           "autostart=true",
           "autorestart=true",
           "startsecs=10",
           "startretries=999",
           "log_stdout=true",
           "log_stderr=true",
           "logfile=/var/log/storm/supervisor.out",
           "logfile_maxbytes=20MB",
           "logfile_backups=10")

    return conf


def generate_master_supervisor_conf(self):
    conf_n = "%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n" % (
        "[program:storm-nimbus]",
        "command=/usr/local/storm/bin/storm nimbus",
        "user=storm",
        "autostart=true",
        "autorestart=true",
        "startsecs=10",
        "startretries=999",
        "log_stdout=true",
        "log_stderr=true",
        "logfile=/var/log/storm/nimbus.out",
        "logfile_maxbytes=20MB",
        "logfile_backups=10\n")
    conf_u = "%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n" % (
        "[program:storm-ui]",
        "command=/usr/local/storm/bin/storm ui",
        "user=storm",
        "autostart=true",
        "autorestart=true",
        "startsecs=10",
        "startretries=999",
        "log_stdout=true",
        "log_stderr=true",
        "logfile=/var/log/storm/ui.out",
        "logfile_maxbytes=20MB",
        "logfile_backups=10")

    return conf_n + conf_u


def generate_zookeeper_conf():
    conf = "%s\n%s\n%s" % ("tickTime=2000", "dataDir=/var/zookeeper",
            "clientPort=2181")
    return conf


def generate_storm_setup_script(env_configs):
    script_lines = ["#!/bin/bash -x"]
    script_lines.append("echo -n > /usr/local/storm/conf/storm.yaml")
    for line in env_configs:
        script_lines.append('echo "%s" >> /usr/local/storm/conf/storm.yaml'
                            % line)

    return "\n".join(script_lines)


def extract_name_values(configs):
    return dict((cfg['name'], cfg['value']) for cfg in configs)


def _set_config(cfg, gen_cfg, name=None):
    if name in gen_cfg:
        cfg.update(gen_cfg[name]['conf'])
    if name is None:
        for name in gen_cfg:
            cfg.update(gen_cfg[name]['conf'])
    return cfg
