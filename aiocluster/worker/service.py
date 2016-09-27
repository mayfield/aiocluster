"""
A service wrapper that provides communication with other workers and the
coordinator.

You can use aiocluster's without this code but will not get the IPC mechs
that allow for remote control and status.
"""

import aiozmq.rpc
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
        await instance.start()
        await instance.wait_stopped()
        await instance.stop()

    def __init__(self, ident, context):
        self.ident = ident
        self.rpc_client = None
        self.rpc_server = None
        super().__init__(context)

    async def start(self):
        await self.start_rpc()

    async def start_rpc(self):
        coord_addr = self.context['coord_rpc_addr']
        worker_addr = 'ipc://%s/worker-rpc-%s' % (self.context['ipc_dir'],
                                                  self.ident)
        c = await aiozmq.rpc.connect_rpc(connect=coord_addr)
        s = await aiozmq.rpc.serve_rpc(RPCHandler(self), bind=worker_addr,
                                       log_exceptions=True)
        self.rpc_client = c
        self.rpc_server = s
        await c.call.register_worker_service(self.ident, str(self),
                                             worker_addr)

    async def stop(self):
        await self.stop_rpc()

    async def stop_rpc(self):
        self.rpc_client.close()
        await self.rpc_client.wait_closed()
        self.rpc_server.close()
        await self.rpc_server.wait_closed()

    async def wait_stopped(self):
        while True:
            print("Nothing to do")
            await asyncio.sleep(10, loop=self.loop)


class RPCHandler(aiozmq.rpc.AttrHandler):

    def __init__(self, worker):
        self.worker = worker
        super().__init__()

    @aiozmq.rpc.method
    def get_status(self):
        logger.info('Handling get_status rpc')
        return 1, 2, 3
