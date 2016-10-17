"""
A service wrapper that provides communication with other workers and the
coordinator.

You can provide your own subclass of a WorkerService or the stock class will
be used if you only provide a cororoutine as the worker function.
"""

import aionanomsg
import asyncio
import cProfile
import functools
import logging
import os
import re

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
        self._profiler_running = False
        if run is not None:
            self.run = functools.partial(run, self)
        self._loop = asyncio.get_event_loop()

    def __str__(self):
        return '<%s ident:%d, pid:%d>' % (type(self).__name__, self.ident,
            self.pid)

    async def __call__(self):
        """ Entrypoint for worker.bootloader.Launcher. """
        await self.setup()
        await self.run()

    async def setup(self):
        await self.start_rpc()

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
        self._loop.create_task(s.start())
        await c.call('register_worker_rpc', self.ident, worker_addr)

    async def start_profiler(self):
        if self._profiler_running:
            return False
        if self._profiler is None:
            self._profiler = cProfile.Profile()
        self._profiler.enable()
        self._profiler_running = True
        return True

    def call_as_dict(self, code):
        """ Parse call tuples from Profile.stats into a dict. """
        if isinstance(code, str):
            file = '~'
            lineno = 0
            func = code
        else:
            file = code.co_filename
            lineno = code.co_firstlineno
            func = code.co_name
        return {
                "file": file,
                "lineno": lineno,
                "function": func
        }

    def stats_as_dict(self, stat):
        """ Parse stats tuples from Profile.stats into a dict. """
        return {
            "callcount": stat.callcount,
            "reccallcount": stat.reccallcount,
            "totaltime": stat.totaltime,
            "inlinetime": stat.inlinetime,
        }

    async def stop_profiler(self):
        if not self._profiler_running:
            return False
        if self._profiler is not None:
            self._profiler.disable()
        self._profiler_running = False
        return True

    async def report_profiler(self):
        if self._profiler is None:
            raise TypeError('Profiler Not Running')
        return [{
            "call": self.call_as_dict(stat.code),
            "stats": self.stats_as_dict(stat),
            "callers": [{
                "call": self.call_as_dict(substat.code),
                "stats": self.stats_as_dict(substat)
            } for substat in (stat.calls or [])]
        } for stat in self._profiler.getstats()]
