#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
# Copyright (C) 2017: Andrey Skvortsov
#
# See COPYING file for copyrights details.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


import getopt
import locale
import os
import shlex
import sys
import threading

import beremiz_runtime.utils.paths as paths
from beremiz_runtime import __version__
from beremiz_runtime.beremiz_service import BeremizService
from beremiz_runtime.i18n import _
from beremiz_runtime.runtime import LogMessageAndException, PlcStatus
from beremiz_runtime.runtime.monotonic_time import monotonic

try:
    from runtime.spawn_subprocess import Popen
except ImportError:
    from subprocess import Popen

# Matiec's standard library relies on libC's locale-dependent
# string to/from number convertions, but IEC-61131 counts
# on '.' for decimal point. Therefore locale is reset to "C" */
locale.setlocale(locale.LC_NUMERIC, "C")

# In case system time is ajusted, it is better to use
# monotonic timers for timers and other timeout based operations.
# hot-patch threading module to force using monitonic time for all
# Thread/Timer/Event/Condition
threading._time = monotonic

beremiz_dir = paths.AbsDir(__file__)


def LogException(*exp):
    LogMessageAndException("", exp)


sys.excepthook = LogException


def version():
    print(_("Beremiz_service: "), __version__)


def usage():
    version()
    print(
        """
Usage of Beremiz PLC execution service :\n
%s {[-n servicename] [-i IP] [-p port] [-x enabletaskbar] [-a autostart]|-h|--help} working_dir
  -n  service name (default:None, zeroconf discovery disabled)
  -i  IP address of interface to bind to (default:localhost)
  -p  port number default:3000
  -h  print this help text and quit
  -a  autostart PLC (0:disable 1:enable) (default:0)
  -x  enable/disable wxTaskbarIcon (0:disable 1:enable) (default:1)
  -t  enable/disable Twisted web interface (0:disable 1:enable) (default:1)
  -w  web server port or "off" to disable web server (default:8009)
  -c  WAMP client config file (can be overriden by wampconf.json in project)
  -s  PSK secret path (default:PSK disabled)
  -e  python extension (absolute path .py)

           working_dir - directory where are stored PLC files
"""
        % sys.argv[0]
    )


def status_change_call_factory(wanted, args):
    def status_change_call(status):
        if wanted is None or status is wanted:
            cmd = shlex.split(args.format(status))
            Popen(cmd)

    return status_change_call


def run():

    # default values
    interface = ""
    port = 3000
    webport = 8009
    PSKpath = None
    wampconf = None
    servicename = None
    autostart = False
    # enablewx = False
    # havewx = False
    enabletwisted = True
    # havetwisted = False

    extensions = []
    statuschange = []

    WorkingDir = None

    try:
        opts, argv = getopt.getopt(
            sys.argv[1:],
            "i:p:n:x:t:a:w:c:e:s:h",
            ["help", "version", "status-change=", "on-plc-start=", "on-plc-stop="],
        )
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit()
        if o == "--version":
            version()
            sys.exit()
        if o == "--on-plc-start":
            statuschange.append(status_change_call_factory(PlcStatus.Started, a))
        elif o == "--on-plc-stop":
            statuschange.append(status_change_call_factory(PlcStatus.Stopped, a))
        elif o == "--status-change":
            statuschange.append(status_change_call_factory(None, a))
        elif o == "-i":
            if len(a.split(".")) == 4:
                interface = a
            elif a == "localhost":
                interface = "127.0.0.1"
            else:
                usage()
                sys.exit()
        elif o == "-p":
            # port: port that the service runs on
            port = int(a)
        elif o == "-n":
            servicename = a
        # elif o == "-x":
        #     enablewx = int(a)
        elif o == "-t":
            enabletwisted = int(a)
        elif o == "-a":
            autostart = int(a)
        elif o == "-w":
            webport = None if a == "off" else int(a)
        elif o == "-c":
            wampconf = None if a == "off" else a
        elif o == "-s":
            PSKpath = None if a == "off" else a
        elif o == "-e":
            fnameanddirname = list(os.path.split(os.path.realpath(a)))
            fnameanddirname.reverse()
            extensions.append(fnameanddirname)
        else:
            usage()
            sys.exit()

    if len(argv) > 1:
        usage()
        sys.exit()
    elif len(argv) == 1:
        WorkingDir = argv[0]
        os.chdir(WorkingDir)
    elif len(argv) == 0:
        WorkingDir = os.getcwd()

    srv = BeremizService(
        servicename=servicename,
        workdir=WorkingDir,
        pskpath=PSKpath,
        autostart=autostart,
        port=port,
        enablewebinterface=enabletwisted,
        webinterface=interface,
        webport=webport,
        extensions=extensions,
        statuschange=statuschange,
        wampconf=wampconf,
    )

    srv.init()

    srv.run()


if __name__ == "__main__":
    run()
