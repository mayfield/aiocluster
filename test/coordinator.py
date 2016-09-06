
import asyncio
import shellish.logging
import signal
import time
from . import base
from aiocluster import coordinator

import logging
root = logging.getLogger()
root.setLevel(20)
root.addHandler(shellish.logging.VTMLHandler())



def worker_entry(ident, context):
    while True:
        time.sleep(5)
        print("Worker still alive")


def ignore_term(ident, context):
    print("ignore term")
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    while True:
        time.sleep(5)
        print("Worker still alive")


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
        await c.start()
        await asyncio.sleep(1)  # XXX Hack until we can wait using RPC.
        await c.stop()
