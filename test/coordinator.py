
import asyncio
import shellish.logging
import signal
import time
from . import base
from aiocluster import coordinator, worker

import logging
root = logging.getLogger()
root.setLevel(20)
root.addHandler(shellish.logging.VTMLHandler())



def worker_entry(ident, context):
    while True:
        time.sleep(5)
        print("worker_entry still alive")


def ignore_term(ident, context):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    while True:
        time.sleep(5)
        print("ignore_term still alive")


def quick_exit(ident, context):
    pass


class CoordinatorTests(base.AIOTestCase):

    async def test_quick_start_stop(self, loop=None):
        c = coordinator.Coordinator('test.coordinator:worker_entry',
                                    worker_count=1, loop=loop)
        await c.start()
        await c.stop()

    async def test_earlyexit_start_stop(self, loop=None):
        c = coordinator.Coordinator('test.coordinator:worker_entry',
                                    worker_count=10, loop=loop)
        await c.start()
        await c.stop()

    async def test_requires_kill(self, loop=None):
        c = coordinator.Coordinator('test.coordinator:ignore_term',
                                    worker_count=2, loop=loop)
        c.term_timeout = 0.500
        await c.start()
        await asyncio.sleep(1, loop=loop)  # XXX Hack until we can wait using RPC.
        await c.stop()

    async def test_restart_worker(self, loop=None):
        c = coordinator.Coordinator('test.coordinator:quick_exit',
                                    worker_count=1, loop=loop)
        offt = next(worker.WorkerProcess.identer)
        await c.start()
        for i in range(100):
            if c.workers[-1].ident > offt:
                break
            await asyncio.sleep(0.100, loop=loop)
            print("WAIT!")
        else:
            raise Exception("Worker restart never detected")
        await c.stop()

    async def test_stop_of_dieing_worker(self, loop=None):
        c = coordinator.Coordinator('test.coordinator:quick_exit',
                                    worker_count=1, loop=loop)
        offt = next(worker.WorkerProcess.identer)
        await c.start()
        for i in range(100):
            if c.workers[-1].ident > offt:
                break
            await asyncio.sleep(0.100, loop=loop)
            print("WAIT!")
        else:
            raise Exception("Worker restart never detected")
        await c.stop()
