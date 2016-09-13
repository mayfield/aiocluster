"""
Coordinator service manages worker processes and acts as a broker for RPC calls
made by foreign coordinator nodes.
"""

import aiozmq.rpc
import asyncio
import logging
import math
import os
import signal
import uuid
from  multiprocessing import cpu_count
from . import service, worker

logger = logging.getLogger('coordinator')


class Coordinator(service.AIOService):

    term_timeout = 5
    kill_timeout = 1

    def __init__(self, worker_spec, worker_count=None,
                 worker_settings=None, handle_sigterm=True,
                 handle_sigint=True, loop=None, **kwargs):
        self.worker_spec = worker_spec
        self.worker_count = worker_count or cpu_count()
        self.worker_settings = worker_settings or {}
        self.workers = []
        self.monitors = []
        self.handle_sigterm = handle_sigterm
        self.handle_sigint = handle_sigint
        self._stopping = False
        self._stopped = asyncio.Event(loop=loop)
        self.ident = '%x' % uuid.uuid4().node
        self.rpc_server = None
        super().__init__(loop=loop, **kwargs)

    async def start(self):
        assert not self._stopping
        logger.debug('Coordinator Starting')
        self.add_signal_handlers()
        await self.start_rpc()
        await self.start_workers()
        logger.info("Coordinator Started")

    async def start_rpc(self):
        """ Setup a zeromq service for rpc with workers. """
        addr = 'ipc://aiocluster-%s-rpc' % self.ident
        self.context['coord_rpc_addr'] = addr
        s = await aiozmq.rpc.serve_rpc(RPCHandler(self), bind=addr,
                                       log_exceptions=True)
        self.rpc_server = s

    async def stop_rpc(self):
        self.rpc_server.close()
        await self.rpc_server.wait_closed()
        self.rpc_server = None

    async def start_workers(self):
        logger.info("Starting %d workers" % self.worker_count)
        try:
            for i in range(self.worker_count):
                await self.start_worker()
        except:
            logger.critical("Failed to start workers!")
            await self.stop()
            raise

    def add_signal_handlers(self):
        if self.handle_sigterm:
            handler = self.create_exit_sighandler(signal.SIGTERM)
            self.loop.add_signal_handler(signal.SIGTERM, handler)
        if self.handle_sigint:
            handler = self.create_exit_sighandler(signal.SIGINT)
            self.loop.add_signal_handler(signal.SIGINT, handler)

    def remove_signal_handlers(self):
        if self.handle_sigterm:
            self.loop.remove_signal_handler(signal.SIGTERM)
        if self.handle_sigint:
            self.loop.remove_signal_handler(signal.SIGINT)

    async def start_worker(self):
        """ Create a worker process and start monitoring it. """
        wp = await worker.spawn(self.worker_spec,
                                settings=self.worker_settings,
                                context=self.context, loop=self.loop)
        mt = self.loop.create_task(self.worker_monitor_wrap(wp))
        wp.monitor_task = mt
        self.workers.append(wp)
        self.monitors.append(mt)

    async def wait_stopped(self):
        """ Block until the coordinator and its workers are stopped. """
        await self._stopped.wait()

    async def stop(self):
        """ Stop the coordinator which in turn kills worker processes.  If the
        coordinator is already being stopped this call will wait until the
        prior call completes;  This consolidates stop behavior for graceful
        shutdown and signal based shutdown. """
        if self._stopping:
            await self._stopped.wait()
            return
        logger.warning("Coordinator stopping")
        self._stopping = True
        self.remove_signal_handlers()
        for x in self.workers:
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
                for x in self.workers:
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
                    undead = [x.process.pid for x in self.workers]
                    logger.critical("Detected %d zombie workers: %s" % (
                                    len(pending), ', '.join(undead)))
                    for x in pending:
                        logger.warning("Cancelling: %s" % x)
                        x.cancel()
        elif self.workers:
            raise RuntimeError('unexpected workers/monitors mismatch')
        await self.stop_rpc()
        logger.info("Coordinator Stopped")
        self._stopped.set()

    def create_exit_sighandler(self, sig):
        """ Return a signal handler that will force a stop and then resend the
        the signal once we are stopped. """

        def handler():
            logger.warning("Caught %s" % sig)
            self.loop.remove_signal_handler(sig)
            stopped = self.loop.create_task(self._stopped.wait())
            stopped.add_done_callback(lambda _: os.kill(0, sig))
            if not self._stopping:
                logger.warning("Forcing coordinator stop from signal handler")
                self.loop.create_task(self.stop())
        return handler

    async def worker_monitor_wrap(self, wp):
        """ Ensure errors from the monitor do not go unnoticed. """
        try:
            await self.worker_monitor(wp)
        except:
            logger.exception("Unrecoverable Worker Monitor Error")
            if not self._stopping:
                self.loop.create_task(self.stop())

    async def worker_monitor(self, wp):
        """ Background task that babysits a worker process and signals us on
        exit/failure. """
        retcode = await wp.process.wait()
        if retcode:
            logger.warning("Non-zero retcode (%d) from: %s" % (retcode, wp))
        self.workers.remove(wp)
        self.monitors.remove(wp.monitor_task)
        wp.monitor_task = None
        await self.on_worker_exit(wp)

    async def worker_restart_delay(self, wp):
        """ Delay a worker restart here to avoid spinning out of control if
        there is trouble starting workers.  This version throttles more as
        worker count goes up.  Subclasses may tweak the behavior as they see
        fit. """
        delay = math.log(1 + wp.ident) ** 2
        logger.info("Delaying worker restart %d seconds" % round(delay))
        await asyncio.sleep(delay, loop=self.loop)

    async def on_worker_exit(self, wp):
        if self._stopping:
            return
        await self.worker_restart_delay(wp)
        await self.start_worker()


class RPCHandler(aiozmq.rpc.AttrHandler):

    def __init__(self, coord):
        self.coord = coord
        super().__init__()

    @aiozmq.rpc.method
    async def register_worker_service(self, worker_ident, desc, rpc_addr):
        logger.info("Confirmed Worker Service!: %s %s %s" % (worker_ident,
            desc, rpc_addr))
