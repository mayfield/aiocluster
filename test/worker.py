
import unittest
import uvloop
from . import base
from aiocluster import worker


def bootloader_test_fn(service, a):
    raise SystemExit(a)


def bootloader_test_fn2(service, *, a=None):
    raise SystemExit(a)


class SpawnTests(base.AIOTestCase):

    async def test_bootloader_loop_arg(self, loop=None):
        wp = await worker.spawn('test.worker.bootloader_test_fn', args=(123,),
                                loop=loop)
        self.assertEqual(await wp.process.wait(), 123)

    async def test_bootloader_loop_kwarg(self, loop=None):
        wp = await worker.spawn('test.worker.bootloader_test_fn2',
                                kwargs={"a": 123}, loop=loop)
        self.assertEqual(await wp.process.wait(), 123)

    async def test_bad_modules(self, loop=None):
        settings = {"error_verbosity": 'pretty'}
        wp = await worker.spawn('doestnotexist.func', settings=settings,
                                loop=loop)
        self.assertEqual(await wp.process.wait(), 1)


@unittest.skip('asyncio child watcher issue24837')
class SpawnNonDefaultIOLoop(SpawnTests):
    set_default_event_loop = False


class SpawnTestsUVLoop(SpawnTests):
    set_default_event_loop = False
    def get_event_loop(self):
        return uvloop.new_event_loop()
