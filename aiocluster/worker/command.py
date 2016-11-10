"""
You can provide your own subclass of a WorkerCommand or the stock class will
be used if you only provide a cororoutine as the worker function.

NOTES:

    plugin ideas:
    --------
    Scheduler service
    Job managment
    Diagnostics (bundled in the rpc plugin now)
    Discovery hooks
    Internal load balancing, sheding and flowcontrol (maybe multiple things)

    plugin deps.  diag requires rpc, etc.
"""

import aionanomsg
import asyncio
import logging
import shellish
from ..diag.worker import profiler, memory

logger = logging.getLogger('worker.command')
_plugins = {}



class WorkerCommand(shellish.Command):
    """ Lifecycle management for the meat and potatos side of an AIO
    service. """

    def __init__(self, *, ident=None, config=None, loop=None, **kwargs):
        self.ident = ident
        self.config = config or {}
        self._loop = loop
        plugins = self.config.get('plugins', [])
        self._plugins = dict((x, _plugins[x](self, loop)) for x in plugins)
        super().__init__(**kwargs)

    def run_wrap(self, args):
        """ Awaitable support for run() and plugin support. """
        for name, plugin in self._plugins.items():
            logger.info("Starting plugin: %s" % name)
            self._loop.run_until_complete(plugin())
        self.fire_event('prerun', args)
        self.prerun(args)
        try:
            result = self.run(args)
            if asyncio.iscoroutine(result):
                result = self._loop.run_until_complete(result)
        except (SystemExit, Exception) as e:
            self.postrun(args, exc=e)
            self.fire_event('postrun', args, exc=e)
            raise e
        else:
            self.postrun(args, result=result)
            self.fire_event('postrun', args, result=result)
            return result


class RPCPlugin(object):
    """ RPC management for the meat and potato's side of an AIO
    command. """

    def __init__(self, worker, loop):
        self._worker_ident = worker.ident
        self._loop = loop
        self._ipc_dir = worker.config['ipc_dir']
        self._coord_rpc_addr = worker.config['coord_rpc_addr']
        self._coord_rpc_client = aionanomsg.RPCClient(aionanomsg.NN_REQ)
        self._worker_rpc_server = aionanomsg.RPCServer(aionanomsg.NN_REP)
        self._worker_rpc_calls_preinit = []
        profiler.ProfilerRPCHandler(self)
        memory.MemoryRPCHandler(self)

    async def __call__(self):
        self._coord_rpc_client.connect(self._coord_rpc_addr)
        for callback, name in self._worker_rpc_calls_preinit:
            self._worker_rpc_server.add_call(callback, name=name)
        self._worker_rpc_calls_preinit = None
        server_addr = 'ipc://%s/worker-rpc-%s' % (self._ipc_dir,
            self._worker_ident)
        self._worker_rpc_server.bind(server_addr)
        self._loop.create_task(self._worker_rpc_server.start())
        await self.coord_rpc_call('register_worker_rpc', self._worker_ident,
                                  server_addr)

    async def coord_rpc_call(self, call, *args, **kwargs):
        return await self._coord_rpc_client.call(call, *args, **kwargs)

    def add_handler(self, name, callback):
        # assert self._worker_rpc_calls_preinit is None, "let's not do this"
        if self._worker_rpc_calls_preinit is not None:
            self._worker_rpc_calls_preinit.append((callback, name))
        else:
            self._worker_rpc_server.add_call(callback, name=name)

_plugins['rpc'] = RPCPlugin
