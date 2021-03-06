# Copyright (c) 2014 Mirantis Inc.
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

from sahara import context
from sahara.openstack.common import log as logging
from sahara.plugins.general import exceptions as ex
from sahara.plugins.vanilla.hadoop2 import config_helper as c_helper
from sahara.plugins.vanilla import utils as vu
from sahara.utils import files
from sahara.utils import general as g

LOG = logging.getLogger(__name__)


def start_instance(instance):
    processes = instance.node_group.node_processes
    for process in processes:
        if process in ['namenode', 'datanode']:
            start_hadoop_process(instance, process)
        elif process in ['resourcemanager', 'nodemanager']:
            start_yarn_process(instance, process)
        else:
            raise ex.HadoopProvisionError(
                "Process %s is not supported" % process)


def start_hadoop_process(instance, process):
    instance.remote().execute_command(
        'sudo su - -c "hadoop-daemon.sh start %s" hadoop' % process)


def start_yarn_process(instance, process):
    instance.remote().execute_command(
        'sudo su - -c  "yarn-daemon.sh start %s" hadoop' % process)


def start_historyserver(instance):
    instance.remote().execute_command(
        'sudo su - -c "mr-jobhistory-daemon.sh start historyserver" hadoop')


def start_oozie_process(pctx, instance):
    with instance.remote() as r:
        if c_helper.is_mysql_enabled(pctx, instance.node_group.cluster):
            _start_mysql(r)
            sql_script = files.get_file_text(
                'plugins/vanilla/hadoop2/resources/create_oozie_db.sql')
            r.write_file_to('/tmp/create_oozie_db.sql', sql_script)
            _oozie_create_db(r)

        _oozie_share_lib(r)
        _start_oozie(r)


def format_namenode(instance):
    instance.remote().execute_command(
        'sudo su - -c "hdfs namenode -format" hadoop')


def refresh_hadoop_nodes(cluster):
    nn = vu.get_namenode(cluster)
    nn.remote().execute_command(
        'sudo su - -c "hdfs dfsadmin -refreshNodes" hadoop')


def refresh_yarn_nodes(cluster):
    rm = vu.get_resourcemanager(cluster)
    rm.remote().execute_command(
        'sudo su - -c "yarn rmadmin -refreshNodes" hadoop')


def _oozie_share_lib(remote):
    LOG.debug("Sharing Oozie libs")
    # remote.execute_command('sudo su - -c "/opt/oozie/bin/oozie-setup.sh '
    #                        'sharelib create -fs hdfs://%s:8020" hadoop'
    #                        % nn_hostname)

    # TODO(alazarev) return 'oozie-setup.sh sharelib create' back
    # when #1262023 is resolved

    remote.execute_command(
        'sudo su - -c "mkdir /tmp/oozielib && '
        'tar zxf /opt/oozie/oozie-sharelib-*.tar.gz -C '
        '/tmp/oozielib && '
        'hadoop fs -mkdir /user && '
        'hadoop fs -mkdir /user/hadoop && '
        'hadoop fs -put /tmp/oozielib/share /user/hadoop/ && '
        'rm -rf /tmp/oozielib" hadoop')

    LOG.debug("Creating sqlfile for Oozie")
    remote.execute_command('sudo su - -c "/opt/oozie/bin/ooziedb.sh '
                           'create -sqlfile oozie.sql '
                           '-run Validate DB Connection" hadoop')


def _start_mysql(remote):
    LOG.debug("Starting mysql")
    remote.execute_command('/opt/start-mysql.sh')


def _oozie_create_db(remote):
    LOG.debug("Creating Oozie DB Schema...")
    remote.execute_command('mysql -u root < /tmp/create_oozie_db.sql')


def _start_oozie(remote):
    remote.execute_command(
        'sudo su - -c "/opt/oozie/bin/oozied.sh start" hadoop')


def await_datanodes(cluster):
    datanodes_count = len(vu.get_datanodes(cluster))
    if datanodes_count < 1:
        return

    LOG.info("Waiting %s datanodes to start up" % datanodes_count)
    with vu.get_namenode(cluster).remote() as r:
        while True:
            if _check_datanodes_count(r, datanodes_count):
                LOG.info(
                    'Datanodes on cluster %s has been started' %
                    cluster.name)
                return

            context.sleep(1)

            if not g.check_cluster_exists(cluster):
                LOG.info(
                    'Stop waiting datanodes on cluster %s since it has '
                    'been deleted' % cluster.name)
                return


def _check_datanodes_count(remote, count):
    if count < 1:
        return True

    LOG.debug("Checking datanode count")
    exit_code, stdout = remote.execute_command(
        'sudo su -lc "hadoop dfsadmin -report" hadoop | '
        'grep \'Datanodes available:\' | '
        'awk \'{print $3}\'')
    LOG.debug("Datanode count='%s'" % stdout.rstrip())

    return exit_code == 0 and int(stdout) == count
