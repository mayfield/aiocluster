
import asyncio
import unittest


class AIOTestCase(unittest.TestCase):

    set_default_event_loop = True
    event_loop_debug = True

    def __init__(self, methodName=None):
        super().__init__(methodName=methodName)
        self._test_coro = getattr(self, methodName)
        setattr(self, methodName, self._test_coro_wrap)

    def get_event_loop(self):
        return asyncio.new_event_loop()

    def _test_coro_wrap(self):
        loop = self.get_event_loop()
        if self.event_loop_debug:
            loop.set_debug(True)
        if self.set_default_event_loop:
            asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._test_coro(loop=loop))
        finally:
            if self.set_default_event_loop:
                asyncio.set_event_loop(None)
            loop.close()
