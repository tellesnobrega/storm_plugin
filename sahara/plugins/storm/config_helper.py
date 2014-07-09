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
from sahara.plugins.general import utils
from sahara.plugins import provisioning as p
from sahara.topology import topology_helper as topology
from sahara.utils import types as types


conductor = c.API
LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def get_config_value(service, name, cluster=None):
    if cluster:
        for ng in cluster.node_groups:
            if (ng.configuration().get(service) and
                    ng.configuration()[service].get(name)):
                return ng.configuration()[service][name]

    for c in PLUGIN_CONFIGS:
        if c.applicable_target == service and c.name == name:
            return c.default_value

    raise RuntimeError("Unable to get parameter '%s' from service %s",
                       name, service)


def generate_storm_config(configs, master_hostname, zk_hostnames):
    
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


def generate_storm_setup_script(env_configs):
    script_lines = ["#!/bin/bash -x"]
    script_lines.append("echo -n > /usr/local/storm/conf/storm.yaml")
    for line in env_configs:
        script_lines.append('echo "%s" >> /usr/local/storm/conf/storm.yaml'
                            % line)

    return "\n".join(script_lines)


def generate_hosts_setup_script(instances):
    # creates a script to add the ips and hostnames of machines
    # to /etc/hosts of all instances of the cluster
    script_lines = ["#!/bin/bash -x"]
    for line in instances:
        script_lines.append('echo "%s %s" >> /etc/hosts' % line
                                % env_configs[line])

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


def get_decommissioning_timeout(cluster):
    return _get_general_cluster_config_value(cluster, DECOMISSIONING_TIMEOUT)


def get_port_from_config(service, name, cluster=None):
    address = get_config_value(service, name, cluster)
    return utils.get_port_from_address(address)
