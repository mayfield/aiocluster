"""
Coordinator service manages worker processes and acts as a broker for RPC calls
made by foreign coordinator nodes.
"""

import aionanomsg
import asyncio
import logging
import math
import os
import signal
import tempfile
import uuid
from  multiprocessing import cpu_count
from . import worker, diag

logger = logging.getLogger('coordinator')
_default_coordinator = None


def get_coordinator():
    """ Singleton like factory for a Coordinator object. """
    if _default_coordinator is None:
        raise RuntimeError('No coordinator initialized')
    return _default_coordinator


class Coordinator(object):

    term_timeout = 1
    kill_timeout = 1

    def __init__(self, worker_spec, worker_count=None, worker_settings=None,
                 worker_config=None, worker_args=None, worker_restart=True,
                 diag_settings=None, handle_sigterm=True, handle_sigint=True,
                 loop=None, set_default=True):
        if set_default:
            global _default_coordinator
            if _default_coordinator is not None:
                raise TypeError('Default coordinator already set')
            _default_coordinator = self
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self.worker_spec = worker_spec
        self.worker_count = worker_count or cpu_count()
        self.worker_restart = worker_restart
        self._worker_config = {
            "plugins": ['rpc']
        }
        self._worker_config.update(worker_config or {})
        self._worker_settings = worker_settings
        self._worker_args = worker_args
        self.diag_settings = diag_settings
        self.workers = {}
        self.monitors = []
        self.handle_sigterm = handle_sigterm
        self.handle_sigint = handle_sigint
        self._stopping = False
        self._stopped = asyncio.Event(loop=loop)
        self.ident = '%x' % uuid.uuid4().node
        self.rpc_server = None
        self.diag = None
        self._ipc_dir = None

    async def start(self):
        assert not self._stopping
        logger.debug('Coordinator Starting')
        self.add_signal_handlers()
        await self.start_rpc()
        if self.diag_settings:
            await self.start_diag(**self.diag_settings)
        await self.start_workers()
        logger.info("Coordinator Started")

    async def start_rpc(self):
        """ Setup a service for rpc with workers. """
        self._ipc_dir = tempfile.TemporaryDirectory(prefix='aiocluster-')
        addr = 'ipc://%s/coord-rpc' % self._ipc_dir.name
        self._worker_config['coord_rpc_addr'] = addr
        self._worker_config['ipc_dir'] = self._ipc_dir.name
        self.rpc_server = s = aionanomsg.RPCServer(aionanomsg.NN_REP)
        s.bind(addr)
        s.add_call(self.register_worker_rpc)
        self._loop.create_task(s.start())

    async def stop_rpc(self):
        self.rpc_server.stop()
        await self.rpc_server.wait_stopped()
        self.rpc_server = None
        self._ipc_dir.cleanup()
        self._ipc_dir = None

    async def start_diag(self, **settings):
        self.diag = diag.DiagService(coordinator=self, loop=self._loop,
                                     **settings)
        await self.diag.start()

    async def stop_diag(self):
        await self.diag.stop()

    async def start_workers(self):
        logger.info("Starting %d workers" % self.worker_count)
        try:
            for i in range(self.worker_count):
                await self.start_worker()
        except:
            logger.critical("Failed to start workers!")
            self.stop()
            await self.wait_stopped()
            raise

    def add_signal_handlers(self):
        if self.handle_sigterm:
            handler = self.create_exit_sighandler(signal.SIGTERM)
            self._loop.add_signal_handler(signal.SIGTERM, handler)
        if self.handle_sigint:
            handler = self.create_exit_sighandler(signal.SIGINT)
            self._loop.add_signal_handler(signal.SIGINT, handler)

    def remove_signal_handlers(self):
        if self.handle_sigterm:
            self._loop.remove_signal_handler(signal.SIGTERM)
        if self.handle_sigint:
            self._loop.remove_signal_handler(signal.SIGINT)

    async def start_worker(self):
        """ Create a worker process and start monitoring it. """
        wp = await worker.spawn(self.worker_spec,
                                worker_settings=self._worker_settings,
                                worker_config=self._worker_config,
                                worker_args=self._worker_args,
                                loop=self._loop)
        mt = self._loop.create_task(self.worker_monitor_wrap(wp))
        wp.monitor_task = mt
        self.workers[wp.ident] = wp
        self.monitors.append(mt)

    async def wait_stopped(self):
        """ Block until the coordinator and its workers are stopped. """
        await self._stopped.wait()

    def stop(self):
        """ Issue a coordinator stop which terminates worker processes.
        Use wait_stopped() to wait for completion of this action. """
        if self._stopping:
            return
        self._loop.create_task(self._do_stop())

    async def _do_stop(self):
        logger.warning("Coordinator stopping")
        self._stopping = True
        self.remove_signal_handlers()
        for x in self.workers.values():
            try:
                x.process.terminate()
            except ProcessLookupError:
                pass
        if self.monitors:
            logger.info("Waiting for %d workers to exit" % len(self.monitors))
            pending = (await asyncio.wait(self.monitors,
                                          timeout=self.term_timeout))[1]
            if pending:
                logger.warning("Timeout waiting for %d workers to exit" %
                               len(pending))
                for x in self.workers.values():
                    logger.warning("Killing: %s" % x)
                    try:
                        x.process.kill()
                    except ProcessLookupError:
                        pass
                logger.warning("Waiting for %d workers to reap" %
                               len(self.monitors))
                pending = (await asyncio.wait(self.monitors,
                                              timeout=self.kill_timeout))[1]
                if pending:
                    undead = ', '.join(str(x.process.pid)
                                       for x in self.workers.values())
                    logger.critical("Detected %d zombie workers: %s" % (
                                    len(pending), undead))
                    for x in pending:
                        x.cancel()
        elif self.workers:
            raise RuntimeError('unexpected workers/monitors mismatch')
        await self.stop_rpc()
        if self.diag:
            await self.stop_diag()
            self.diag = None
        logger.info("Coordinator Stopped")
        self._stopped.set()

    def create_exit_sighandler(self, sig):
        """ Return a signal handler that will force a stop and then resend the
        signal once we are stopped. """

        def handler():
            logger.warning("Caught %s" % sig)
            self._loop.remove_signal_handler(sig)
            stopped = self._loop.create_task(self._stopped.wait())
            stopped.add_done_callback(lambda _: os.kill(0, sig))
            if not self._stopping:
                logger.warning("Forcing coordinator stop from signal handler")
                self.stop()
        return handler

    async def worker_monitor_wrap(self, wp):
        """ Ensure errors from the monitor do not go unnoticed. """
        try:
            await self.worker_monitor(wp)
        except asyncio.CancelledError:
            logger.warning("Worker cancelled: %s" % wp)
        except Exception:
            logger.exception("Unrecoverable worker monitor error")
            self.stop()

    async def worker_monitor(self, wp):
        """ Background task that babysits a worker process and signals us on
        exit/failure. """
        retcode = await wp.process.wait()
        if retcode:
            logger.warning("Non-zero retcode (%d) from: %s" % (retcode, wp))
        del self.workers[wp.ident]
        self.monitors.remove(wp.monitor_task)
        wp.monitor_task = None
        await self.maybe_restart_worker(wp)

    async def worker_restart_delay(self, wp):
        """ Delay a worker restart here to avoid spinning out of control if
        there is trouble starting workers.  This version throttles more as
        worker count goes up.  Subclasses may tweak the behavior as they see
        fit. """
        delay = math.log(1 + wp.ident) ** 2
        logger.info("Delaying worker restart %d seconds" % round(delay))
        await asyncio.sleep(delay, loop=self._loop)

    async def maybe_restart_worker(self, wp):
        if self._stopping:
            return
        if not self.worker_restart:
            if not self.workers:
                logger.warning("All workers have quit")
                self.stop()
        else:
            await self.worker_restart_delay(wp)
            await self.start_worker()

    async def register_worker_rpc(self, worker_ident, rpc_addr):
        logger.debug("Registered worker RPC server: %s %s" % (worker_ident,
                     rpc_addr))
        rpc = aionanomsg.RPCClient(aionanomsg.NN_REQ)
        rpc.connect(rpc_addr)
        # XXX Use cleaner technique for adding rpc handler to worker proxy.
        self.workers[worker_ident].rpc = rpc
