import os
import sys
import threading
import traceback
from functools import partial
from threading import Lock, Thread

from twisted.internet import reactor

import beremiz_runtime.runtime as rt
import beremiz_runtime.runtime.NevowServer as NS
import beremiz_runtime.runtime.WampClient as WC
from beremiz_runtime.i18n import _
from beremiz_runtime.runtime import LogMessageAndException, default_evaluator
from beremiz_runtime.runtime.eRPCServer import eRPCServer as RPCServer
from beremiz_runtime.runtime.Stunnel import ensurePSK


class BeremizService:

    _rpc_server = None

    def __init__(
        self,
        servicename,
        workdir,
        pskpath,
        autostart=False,
        port=3000,
        enablewebinterface=True,
        ipaddress="localhost",
        webport=8009,
        extensions=[],
        status_callback=[],
        wampconf=None,
    ):

        self._servicename = servicename
        self._autostart = autostart
        self._port = port
        self._enablewebinterface = enablewebinterface
        self._ipaddress = ipaddress
        self._webport = webport
        self._extensions = extensions
        self._status_callback = status_callback

        self._workdir = workdir
        self._pskpath = pskpath
        self._wampconf = wampconf

    def init(self):

        if not os.path.isdir(self._workdir):
            os.mkdir(self._workdir)

        pyruntimevars = {}

        evaluator = default_evaluator

        self._installThreadExcepthook()

        havewamp = False

        if self._enablewebinterface:
            if self._webport is not None:
                try:
                    NS.WorkingDir = self._workdir
                except Exception:
                    LogMessageAndException(_("Nevow/Athena import failed :"))
                    self._webport = None

            try:
                WC.WorkingDir = self._workdir
                havewamp = True
            except Exception:
                LogMessageAndException(_("WAMP import failed :"))

        # Load extensions
        for extention_file, extension_folder in self._extensions:
            sys.path.append(extension_folder)
            exec(
                compile(
                    open(os.path.join(extension_folder, extention_file), "rb").read(),
                    os.path.join(extension_folder, extention_file),
                    "exec",
                ),
                locals(),
            )

        # Service name is used as an ID for stunnel's PSK
        # Some extension may set 'servicename' to a computed ID or Serial Number
        # instead of using commandline '-n'
        if self._servicename is not None and self._pskpath is not None:
            ensurePSK(self._servicename, self._pskpath)

        rt.CreatePLCObjectSingleton(
            self._workdir, self._status_callback, evaluator, pyruntimevars
        )

        self._rpc_server = RPCServer(self._servicename, self._ipaddress, self._port)

        if self._enablewebinterface:
            if self._webport is not None:
                try:
                    website = NS.RegisterWebsite(self._ipaddress, self._webport)
                    pyruntimevars["website"] = website
                except Exception:
                    LogMessageAndException(_("Nevow Web service failed. "))

            if havewamp:
                try:
                    WC.RegisterWampClient(self._wampconf, self._pskpath)
                    WC.RegisterWebSettings(NS)
                except Exception:
                    LogMessageAndException(_("WAMP client startup failed. "))

        self._rpc_server_thread = None

    def run(self):

        if self._enablewebinterface:

            ui_thread_started = Lock()
            ui_thread_started.acquire()

            reactor.callLater(0, ui_thread_started.release)

            ui_thread = Thread(
                target=partial(reactor.run, installSignalHandlers=False),
                name="UIThread",
            )
            ui_thread.start()

            ui_thread_started.acquire()
            print("UI thread started successfully.")
            try:
                # blocking worker loop
                rt.MainWorker.runloop(self._FirstWorkerJob)
            except KeyboardInterrupt:
                pass
        else:
            try:
                # blocking worker loop
                rt.MainWorker.runloop(self._FirstWorkerJob)
            except KeyboardInterrupt:
                pass

        self._rpc_server.Quit()
        self._rpc_server_thread.join()

        plcobj = rt.GetPLCObjectSingleton()
        try:
            plcobj.StopPLC()
            plcobj.UnLoadPLC()
        except Exception:
            print(traceback.format_exc())

        if self._enablewebinterface:
            reactor.stop()

    def _installThreadExcepthook(self):
        init_old = threading.Thread.__init__

        def init(self, *args, **kwargs):
            init_old(self, *args, **kwargs)
            run_old = self.run

            def run_with_except_hook(*args, **kw):
                try:
                    run_old(*args, **kw)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception:
                    sys.excepthook(*sys.exc_info())

            self.run = run_with_except_hook

        threading.Thread.__init__ = init

    def _FirstWorkerJob(self):

        rpc_thread_started = Lock()
        rpc_thread_started.acquire()
        self._rpc_server_thread = Thread(
            target=self._rpc_server.Loop,
            kwargs=dict(when_ready=rpc_thread_started.release),
            name="RPCThread",
        )

        self._rpc_server_thread.start()

        # Wait for rpc thread to be effective
        rpc_thread_started.acquire()

        self._rpc_server.PrintServerInfo()

        # Beremiz IDE detects LOCAL:// runtime is ready by looking
        # for self.workdir in the daemon's stdout.
        if sys.stdout:
            sys.stdout.write(_("Current working directory :") + self._workdir + "\n")
            sys.stdout.flush()

        rt.GetPLCObjectSingleton().AutoLoad(self._autostart)
