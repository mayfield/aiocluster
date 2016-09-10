"""
A service wrapper that provides communication with other workers and the
coordinator.

You can use aiocluster's without this code but will not get the IPC mechs
that allow for remote control and status.
"""

import asyncio
from .. import service


class WorkerService(service.AIOService):
    """ RPC and lifecycle management for the meat and potato's side of an AIO
    service. """

    name = 'worker'

    @classmethod
    async def factory(cls, ident, context):
        instance = cls(context)
        await instance.start()
        await asyncio.sleep(5)
        print("YES!")
        print("YES!")
        print("YES!")
        print("YES!")

    async def start(self):
        pass
