"""
Coordinator service manages worker processes and acts as a broker for RPC calls
made by foreign coordinator nodes.
"""

import asyncio
import logging
import math
import os
import signal
from  multiprocessing import cpu_count
from . import service, worker

logger = logging.getLogger('coordinator')


class Coordinator(service.AIOService):

    term_timeout = 5
    kill_timeout = 1

    def __init__(self, worker_spec, worker_count=None,
                 worker_exit_action=None, handle_sigterm=True,
                 handle_sigint=True, loop=None, **kwargs):
        self.worker_spec = worker_spec
        self.worker_count = worker_count or cpu_count()
        self.workers = []
        self.monitors = []
        self.handle_sigterm = handle_sigterm
        self.handle_sigint = handle_sigint
        self._stopping = False
        self._stopped = asyncio.Event(loop=loop)
        super().__init__(loop=loop, **kwargs)

    async def start(self):
        assert not self._stopping
        self.add_signal_handlers()
        logger.info("Coordinator starting %d workers" % self.worker_count)
        try:
            for i in range(self.worker_count):
                await self.start_worker()
        except:
            logger.critical("Failed to start coordinator!")
            await self.stop()
            raise
        logger.info("Coordinator Started")

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
        wp = await worker.spawn(self.worker_spec, context=self.context,
                                loop=self.loop)
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
        else:
            logger.warning("Silent death: %s" % wp)
        self.workers.remove(wp)
        self.monitors.remove(wp.monitor_task)
        wp.monitor_task = None
        await self.on_worker_exit(wp)

    async def on_worker_exit(self, wp):
        if self._stopping:
            return
        # Add some delay for spuriously restarting workers. 
        delay = math.log(100 + (1 / max(wp.age().total_seconds(), 1/10000)))
        logger.warning("Replacing dead worker (after %f seconds delay): %s" %
                       (delay, wp))
        await asyncio.sleep(delay, loop=self.loop)
        await self.start_worker()
