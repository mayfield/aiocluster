"""
Abstract base for asyncio network services.
"""

import asyncio


class AIOService(object):
    """ ABC for aysncio service. """

    name = None

    def __init__(self, context=None, loop=None):
        self.context = context or {}
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop

    async def start(self):
        """ Setup and start any network listeners here. """
        raise NotImplementedError("pure virtual")

    def stop(self):
        """ Signal that a stop is to be performed.  This method must be
        idempotent. """
        pass

    async def wait_stopped(self):
        """ Block until service is stopped. """
        pass
