"""
A service wrapper that provides communication with other workers and the
coordinator.

You can provide your own subclass of a WorkerService or the stock class will
be used if you only provide a cororoutine as the worker function.
"""

import aionanomsg
import asyncio
import functools
import logging
import os
import shellish
from ..diag.worker import profiler, memory

logger = logging.getLogger('worker.service')
mixins = {}


class WorkerService(object):
    """ Lifecycle management for the meat and potato's side of an AIO
    service. """


    def __init__(self, ident, context, loop=None, run=None, run_args=None,
                 run_kwargs=None):
        self.ident = ident
        self.pid = os.getpid()
        self._context = context
        if run is not None:
            self.run = functools.partial(run, self)
        self._run_args = run_args or ()
        self._run_kwargs = run_kwargs or {}
        self._loop = loop or asyncio.get_event_loop()
        self.init()

    def __str__(self):
        return '<%s ident:%d, pid:%d>' % (type(self).__name__, self.ident,
            self.pid)

    async def __call__(self):
        """ Entrypoint for worker.bootloader.Launcher. """
        await self.setup()
        await self.run(*self._run_args, **self._run_kwargs)

    def init(self):
        """ Subclasses and mixins can safely place init here. """
        pass

    async def setup(self):
        """ Subclasses and mixins can perform async setup here. """
        pass

    async def run(self):
        raise NotImplementedError()


class RPCWorkerMixin(object):
    """ RPC management for the meat and potato's side of an AIO
    service. """

    def init(self):
        self._coord_rpc_client = aionanomsg.RPCClient(aionanomsg.NN_REQ)
        self._worker_rpc_server = aionanomsg.RPCServer(aionanomsg.NN_REP)
        self._worker_rpc_calls_preinit = []
        super().init()
        profiler.ProfilerRPCHandler(self)
        memory.MemoryRPCHandler(self)

    async def setup(self):
        self._coord_rpc_client.connect(self._context['coord_rpc_addr'])
        for callback, name in self._worker_rpc_calls_preinit:
            self._worker_rpc_server.add_call(callback, name=name)
        self._worker_rpc_calls_preinit = None
        server_addr = 'ipc://%s/worker-rpc-%s' % (self._context['ipc_dir'],
                                                  self.ident)
        self._worker_rpc_server.bind(server_addr)
        self._loop.create_task(self._worker_rpc_server.start())
        await self.coord_rpc_call('register_worker_rpc', self.ident,
                                  server_addr)
        await super().setup()

    async def coord_rpc_call(self, call, *args, **kwargs):
        return await self._coord_rpc_client.call(call, *args, **kwargs)

    def add_worker_rpc_callback(self, callback, name=None):
        """ Extensions can register rpc handlers for this service at init
        time by calling this on the class prior to startup. """
        if self._worker_rpc_calls_preinit is not None:
            self._worker_rpc_calls_preinit.append((callback, name))
        else:
            self._worker_rpc_server.add_call(callback, name=name)

mixins['rpc'] = RPCWorkerMixin


class CLIWorkerMixin(object):
    """ Bring in shellish.Command capability so workers can extend the CLI
    arguments used in the `aiocluster` tool. """

    def init(self):
        self._cli_command = shellish.Command(name='worker')
        super().init()

mixins['cli'] = CLIWorkerMixin
