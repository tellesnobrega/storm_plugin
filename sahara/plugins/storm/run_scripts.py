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

from sahara.openstack.common import log as logging


LOG = logging.getLogger(__name__)


def start_zookeeper(remote):
    remote.execute_command("cd /opt/zookeeper/zookeeper-3.4.6 && bin/zkServer.sh start")


def start_storm_supervisor(slave_nodes):
    for node in slave_nodes:
        node.execute_command("sudo service supervisor start")


def start_storm_nimbus_and_ui(master_node):
    master_node.execute_command("sudo service supervisor start")


def stop_storm_nimbus_and_ui(master_node):
    master_node.execute_command("sudo service supervisor stop")


def stop_storm_supervisor(slave_nodes):
    for node in slave_nodes:
        node.execute_command("sudo service supervisor stop")
