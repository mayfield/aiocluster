"""
Profiler RPC calls for WorkerCommand.
"""

import cProfile
import logging

logger = logging.getLogger('diag.profiler')


class ProfilerRPCHandler(object):

    def __init__(self, rpc_plugin):
        self._profiler = None
        rpc_plugin.add_handler('profiler_set_active', self.set_active)
        rpc_plugin.add_handler('profiler_get_active', self.get_active)
        rpc_plugin.add_handler('profiler_report', self.report)

    async def get_active(self):
        return self._profiler is not None

    async def set_active(self, value):
        """ Return True if the state was changed. """
        activate = bool(value)
        if activate is (self._profiler is not None):
            return False  # did nothing
        if activate:
            logger.warning("Activating Diagnostic Profiler")
            self._profiler = cProfile.Profile()
            self._profiler.enable()
        else:
            logger.warning("Deactivating Diagnostic Profiler")
            self._profiler.disable()
            self._profiler = None
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
