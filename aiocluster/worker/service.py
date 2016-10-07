"""
A service wrapper that provides communication with other workers and the
coordinator.

You can use aiocluster's without this code but will not get the IPC mechs
that allow for remote control and status.
"""

import aionanomsg
import asyncio
import logging
from .. import service

logger = logging.getLogger('worker.service')


class WorkerService(service.AIOService):
    """ RPC and lifecycle management for the meat and potato's side of an AIO
    service. """

    name = 'worker'

    @classmethod
    async def run(cls, *args, **kwargs):
        instance = cls(*args, **kwargs)
        await instance.start_rpc()
        await instance.start()
        await instance.wait_stopped()

    def __init__(self, ident, context):
        self.ident = ident
        self.rpc_client = None
        self.rpc_server = None
        super().__init__(context)

    async def start(self):
        raise NotImplementedError()

    async def start_rpc(self):
        coord_addr = self.context['coord_rpc_addr']
        worker_addr = 'ipc://%s/worker-rpc-%s' % (self.context['ipc_dir'],
                                                  self.ident)
        self.rpc_client = c = aionanomsg.RPCClient(aionanomsg.NN_REQ)
        c.connect(coord_addr)
        self.rpc_server = s = aionanomsg.RPCServer(aionanomsg.NN_REP)
        s.bind(worker_addr)
        self.loop.create_task(s.start())
        await c.call('register_worker_service', self.ident, str(self),
                     worker_addr)

    def stop(self):
        raise NotImplementedError("Stop of worker not supported")

    async def wait_stopped(self):
        while True:
            print("Nothing to do")
            await asyncio.sleep(10, loop=self.loop)
