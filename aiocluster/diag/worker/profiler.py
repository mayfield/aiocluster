"""
Profiler RPC calls for WorkerCommand.
"""

import cProfile


class ProfilerRPCHandler(object):

    def __init__(self, rpc_plugin):
        self._profiler_running = False
        self._profiler = None
        rpc_plugin.add_handler('profiler_start', self.start)
        rpc_plugin.add_handler('profiler_stop', self.stop)
        rpc_plugin.add_handler('profiler_report', self.report)

    async def start(self):
        if self._profiler_running:
            return False
        if self._profiler is None:
            self._profiler = cProfile.Profile()
        self._profiler.enable()
        self._profiler_running = True
        return True

    async def stop(self):
        if not self._profiler_running:
            return False
        if self._profiler is not None:
            self._profiler.disable()
        self._profiler_running = False
        return True

    async def report(self):
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
