
import asyncio
import shellish.logging
import signal
import time
from . import base
from aiocluster import coordinator, worker

import logging
root = logging.getLogger()
root.setLevel(0)
root.addHandler(shellish.logging.VTMLHandler())



def worker_entry(service):
    while True:
        time.sleep(5)
        print("worker_entry still alive")


def ignore_term(service):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    while True:
        time.sleep(5)
        print("ignore_term still alive")


def quick_exit(service):
    pass


async def quick_exit_coro(service):
    pass


def make_coord(*args, **kwargs):
    return coordinator.Coordinator(*args, set_default=False, **kwargs)


class CoordinatorTests(base.AIOTestCase):

    async def test_quick_start_stop(self, loop=None):
        c = make_coord('test.coordinator.worker_entry', worker_count=1,
                       loop=loop)
        await c.start()
        c.stop()
        await c.wait_stopped()

    async def test_earlyexit_start_stop(self, loop=None):
        c = make_coord('test.coordinator.worker_entry', worker_count=10,
                       loop=loop)
        await c.start()
        c.stop()
        await c.wait_stopped()

    async def test_requires_kill(self, loop=None):
        c = make_coord('test.coordinator.ignore_term', worker_count=2,
                       loop=loop)
        c.term_timeout = 0.500
        await c.start()
        await asyncio.sleep(1, loop=loop)  # XXX Hack until we can wait using RPC.
        c.stop()
        await c.wait_stopped()

    async def test_restart_worker(self, loop=None):
        c = make_coord('test.coordinator.quick_exit', worker_count=1,
                       loop=loop)
        offt = next(worker.WorkerProcess.identer)
        await c.start()
        for i in range(1000):
            if next(iter(c.workers.values())).ident > offt:
                break
            await asyncio.sleep(0.010, loop=loop)
        else:
            raise Exception("Worker restart never detected")
        c.stop()
        await c.wait_stopped()

    async def test_coro_worker(self, loop=None):
        c = make_coord('test.coordinator.quick_exit_coro', worker_count=1,
                       loop=loop)
        offt = next(worker.WorkerProcess.identer)
        await c.start()
        for i in range(1000):
            if next(iter(c.workers.values())).ident > offt:
                break
            await asyncio.sleep(0.010, loop=loop)
        else:
            raise Exception("Worker restart never detected")
        c.stop()
        await c.wait_stopped()
