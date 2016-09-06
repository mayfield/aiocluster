"""
Coordinator service manages worker processes and acts as a broker for RPC calls
made by foreign coordinator nodes.
"""

import asyncio
import logging
from  multiprocessing import cpu_count
from . import service, worker

logger = logging.getLogger('coordinator')


class Coordinator(service.AIOService):

    stop_timeout = 5

    def __init__(self, worker_spec, worker_count=cpu_count(),
                 worker_exit_action=None, **kwargs):
        self.worker_spec = worker_spec
        self.worker_count = worker_count
        self.workers = []
        self.monitors = []
        self._stopping = False
        super().__init__(**kwargs)

    async def start(self):
        logger.info("Coordinator starting %d workers" % self.worker_count)
        for i in range(self.worker_count):
            await self.start_worker()
        logger.info("Coordinator Started")

    async def start_worker(self):
        """ Create a worker process and start monitoring it. """
        wp = await worker.spawn(self.worker_spec, context=self.context,
                                loop=self.loop)
        self.workers.append(wp)
        t = self.loop.create_task(self.worker_monitor(wp))
        self.monitors.append(t)

    async def stop(self):
        logger.warning("Coordinator stopping")
        self._stopping = True
        for x in self.workers:
            x.process.terminate()
        monitors = self.monitors[:]
        del self.monitors[:]
        logger.info("Waiting for %d workers to exit" % len(monitors))
        pending = (await asyncio.wait(monitors, timeout=self.stop_timeout))[1]
        if self.workers:
            logger.error("Timeout waiting for workers to exit")
            for x in self.workers:
                logger.warning("Killing: %s" % x)
                x.process.kill()
            for x in pending:
                logger.warning("Cancelling: %s" % x)
                x.cancel()
        del self.workers[:]
        logger.info("Coordinator Stopped")

    async def worker_monitor(self, wp):
        """ Background task that babysits a worker process and signals us on
        exit/failure. """
        retcode = await wp.wait()
        if retcode:
            logger.warning("Non-zero retcode (%d) from worker: %s" % (retcode,
                           wp))
        self.workers.remove(wp)
        await self.on_worker_exit(wp)

    async def on_worker_exit(self, wp):
        if self._stopping:
            return
        logger.warning("Replacing dead worker: %s" % wp)
        self.start_worker()
