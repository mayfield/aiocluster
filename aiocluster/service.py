"""
Abstract base for asyncio network services.
"""

import asyncio


class AIOService(object):
    """ ABC for aysncio service. """

    name = None

    def __init__(self, context=None, loop=None):
        self.context = context
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop

    async def start(self):
        """ Setup and start any network listeners here. """
        raise NotImplementedError("pure virtual")

    async def cleanup(self):
        """ Perform any ioloop cleanup here. """
        raise NotImplementedError("pure virtual")
