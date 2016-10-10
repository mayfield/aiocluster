"""
A service wrapper that provides communication with other workers and the
coordinator.

You can provide your own subclass of a WorkerService or the stock class will
be used if you only provide a cororoutine as the worker function.
"""

import aionanomsg
import asyncio
import functools
import io
import logging
import os
import pstats

logger = logging.getLogger('worker.service')


class WorkerService(object):
    """ RPC and lifecycle management for the meat and potato's side of an AIO
    service. """

    def __init__(self, ident, context, run=None):
        self.ident = ident
        self.pid = os.getpid()
        self.rpc_client = None
        self.rpc_server = None
        self.context = context
        self._profiler = None
        if run is not None:
            self.run = functools.partial(run, self)
        self.loop = asyncio.get_event_loop()

    def __str__(self):
        return '<%s ident:%d, pid:%d>' % (type(self).__name__, self.ident,
            self.pid)

    async def __call__(self):
        """ Entrypoint for worker.bootloader.Launcher. """
        await self.setup()
        await self.run()

    async def setup(self):
        await self.start_rpc()  # XXX: I don't like this language

    async def run(self):
        raise NotImplementedError()

    async def start_rpc(self):
        coord_addr = self.context['coord_rpc_addr']
        worker_addr = 'ipc://%s/worker-rpc-%s' % (self.context['ipc_dir'],
                                                  self.ident)
        self.rpc_client = c = aionanomsg.RPCClient(aionanomsg.NN_REQ)
        c.connect(coord_addr)
        self.rpc_server = s = aionanomsg.RPCServer(aionanomsg.NN_REP)
        s.add_call(self.start_profiler)
        s.add_call(self.stop_profiler)
        s.add_call(self.report_profiler)
        s.bind(worker_addr)
        self.loop.create_task(s.start())
        await c.call('register_worker_rpc', self.ident, worker_addr)

    async def start_profiler(self):
        import cProfile
        if self._profiler is not None:
            raise RuntimeError('profiler already started')
        self._profiler = cProfile.Profile()
        self._profiler.enable()

    def call_as_dict(self, call):
        """ Parse call tuples from Profile.stats into a dict. """
        return {
                "file": call[0],
                "lineno": call[1],
                "function": call[2]
        }

    def stats_as_dict(self, stats):
        """ Parse stats tuples from Profile.stats into a dict. """
        return {
            "calls": stats[0],
            "primitive_calls": stats[1],
            "total": stats[2],
            "cumulative": stats[3],
        }

    async def stop_profiler(self):
        if self._profiler is None:
            raise RuntimeError('profiler never started')
        self._profiler.disable()

    async def report_profiler(self):
        #self._profiler.create_stats()
        self._profiler.snapshot_stats()
        data = [{
            "call": self.call_as_dict(call),
            "stats": self.stats_as_dict(stats),
            "callers": [{
                "call": self.call_as_dict(k),
                "stats": self.stats_as_dict(stats)
            } for k, v in stats[-1].items()]
        } for call, stats in self._profiler.stats.items()]
        return data
