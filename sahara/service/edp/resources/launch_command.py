#!/usr/bin/env python

# Copyright (c) 2014 OpenStack Foundation
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

import logging
import signal
import subprocess
import sys

log = logging.getLogger()
hdlr = logging.FileHandler(sys.argv[0]+".log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)


def make_handler(a):
    def handle_signal(signum, stack):
        a.send_signal(signum)
        log.info("Sent SIGINT to subprocess")
    return handle_signal

log.info("Running %s" % ' '.join(sys.argv[1:]))

try:
    # "Unignore" SIGINT before the subprocess is launched
    # in case this process is running in the background
    # (background processes ignore SIGINT)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Interpret all command line args as the command to run
    a = subprocess.Popen(sys.argv[1:],
                         stdout=open("stdout", "w"),
                         stderr=open("stderr", "w"))

    # Set our handler to trap SIGINT and propagate to the child
    # The expectation is that the child process handles SIGINT
    # and exits.
    signal.signal(signal.SIGINT, make_handler(a))

    # Write out the childpid just in case there is a
    # need to send special signals directly to the child process
    open("childpid", "w").write("%s\n" % a.pid)

    # Wait for child to exit and write result file
    log.info("Waiting for subprocess %s" % a.pid)
    ret = a.wait()
    log.info("Subprocess exit status %s" % ret)
    open("result", "w").write("%s\n" % ret)

except Exception as e:
    log.exception(e)
