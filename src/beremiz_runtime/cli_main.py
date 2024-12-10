"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         fibonacci = beremiz_runtime.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``fibonacci`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This file can be renamed depending on your needs or safely removed if not needed.

References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import argparse
import locale
import logging
import os
import shlex
import sys
import threading

from beremiz_runtime import __version__
from beremiz_runtime.beremiz_service import BeremizService
from beremiz_runtime.runtime import LogMessageAndException, PlcStatus
from beremiz_runtime.runtime.monotonic_time import monotonic

try:
    from runtime.spawn_subprocess import Popen
except ImportError:
    from subprocess import Popen

_logger = logging.getLogger(__name__)


# Matiec's standard library relies on libC's locale-dependent
# string to/from number convertions, but IEC-61131 counts
# on '.' for decimal point. Therefore locale is reset to "C" */
locale.setlocale(locale.LC_NUMERIC, "C")

# In case system time is ajusted, it is better to use
# monotonic timers for timers and other timeout based operations.
# hot-patch threading module to force using monitonic time for all
# Thread/Timer/Event/Condition
threading._time = monotonic


def LogException(*exp):
    LogMessageAndException("", exp)


sys.excepthook = LogException

# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Beremiz PLC runtime")
    parser.add_argument(
        "--version",
        action="version",
        version=f"beremiz-runtime {__version__}",
    )
    # parser.add_argument(dest="n", help="n-th Fibonacci number", type=int, metavar="INT")
    parser.add_argument(
        "-n",
        "--name",
        dest="servicename",
        type=str,
        default=None,
        help="Service name (default:None, zeroconf discovery disabled)",
    ),
    parser.add_argument(
        "-i",
        "--ip",
        dest="ipaddress",
        type=str,
        default="localhost",
        help="IP address of interface to bind to (default:localhost)",
    ),
    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        default=3000,
        help="Port that the service runs on default:3000",
    ),
    parser.add_argument(
        "-a",
        "--autostart",
        dest="autostart",
        help="autostart PLC (default:False)",
        action="store_true",
    ),
    parser.add_argument(
        "-t",
        "--web",
        dest="enablewebinterface",
        type=bool,
        default=True,
        help="Enable Twisted web interface (default:True)",
    ),
    parser.add_argument(
        "-w",
        "--wport",
        dest="webport",
        type=int,
        default=8009,
        help="Web server port (default:8009)",
    ),
    parser.add_argument(
        "-s",
        "--pskpath",
        dest="pskpath",
        type=str,
        default=None,
        help="PSK secret path (default:PSK disabled)",
    ),
    parser.add_argument(
        "-c",
        "--wampconf",
        dest="wampconf",
        type=str,
        default=None,
        help="WAMP client config file (can be overriden by wampconf.json in project)",
    ),
    parser.add_argument(
        "-e",
        "--pyext",
        dest="pyextensions",
        type=list,
        default=[],
        action="append",
        help="Python extensions (absolute path to .py) can be used multiple times",
    ),
    parser.add_argument(
        "-d",
        "--workdir",
        dest="workdir",
        type=str,
        default=os.getcwd(),
        help=f"Working directory (default:{os.getcwd()})",
    ),
    parser.add_argument(
        "--on-plc-start",
        dest="onplcstart",
        type=str,
        default=None,
        help="Callback process on PLC start",
    ),
    parser.add_argument(
        "--on-plc-stop",
        dest="onplcstop",
        type=str,
        default=None,
        help="Callback process on PLC stop",
    ),
    parser.add_argument(
        "--on-status-change",
        dest="onstatuschange",
        type=str,
        default=None,
        help="Callback process on PLC status change",
    ),
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def status_change_call_factory(wanted, args):
    def status_change_call(status):
        if wanted is None or status is wanted:
            cmd = shlex.split(args.format(status))
            Popen(cmd)

    return status_change_call


def main(args):
    """Wrapper allowing :func:`fib` to be called with string arguments in a CLI fashion

    Instead of returning the value from :func:`fib`, it prints the result to the
    ``stdout`` in a nicely formatted message.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    _logger.debug("Starting Beremiz runtime...")

    statuschange = []

    if args.onplcstart:
        statuschange.append(
            status_change_call_factory(PlcStatus.Stopped, args.onplcstart)
        )
    if args.onplcstop:
        statuschange.append(status_change_call_factory(None, args.onplcstop))
    if args.onstatuschange:
        statuschange.append(
            status_change_call_factory(PlcStatus.Started, args.onstatuschange)
        )

    srv = BeremizService(
        servicename=args.servicename,
        workdir=args.workdir,
        pskpath=args.pskpath,
        autostart=args.autostart,
        port=args.port,
        enablewebinterface=args.enablewebinterface,
        ipaddress=args.ipaddress,
        webport=args.webport,
        extensions=args.pyextensions,
        status_callback=statuschange,
        wampconf=args.wampconf,
    )

    srv.init()

    srv.run()

    _logger.info("Beremiz runtime stopped.")


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m beremiz_runtime.cli_main 42
    #
    run()
