"""
/api/v1/about handler for info about this execution of aiocluster.
"""

import asyncio
import datetime
import os
import platform
import psutil
from .. import util
from .... import coordinator

psutil.cpu_percent(interval=None)  # seed


class AboutResource(util.Resource):
    """ Information about this AIOCluster stack and platform. """

    use_docstring = True

    async def get(self, request):
        try:
            return self._cache
        except AttributeError:
            self._cache = c =  self._get()
            return c

    def _get(self):
        coord = coordinator.get_coordinator()
        evpolicy = type(asyncio.get_event_loop_policy())
        evloop = type(coord._loop)
        return {
            "event_loop": {
                "policy": '%s.%s' % (evpolicy.__module__, evpolicy.__name__),
                "debug": coord._loop.get_debug(),
                "loop": '%s.%s' % (evloop.__module__, evloop.__name__),
            },
            "coord": {
                "ident": coord.ident,
                "worker_spec": coord.worker_spec,
                "worker_count": coord.worker_count,
                "worker_args": coord._worker_args,
                "worker_config": coord._worker_config,
                "worker_settings": coord._worker_settings,
                "diag_settings": coord.diag_settings,
                "handle_sigint": coord.handle_sigint,
                "handle_sigterm": coord.handle_sigterm,
                "term_timeout": coord.term_timeout,
                "kill_timeout": coord.kill_timeout,
            },
            "system": {
                "system": platform.system(),
                "machine": platform.machine(),
                "python_implementation": platform.python_implementation(),
                "python_version": platform.python_version(),
                "cpu_count": os.cpu_count(),
                "boot_time": '%sZ' % datetime.datetime.fromtimestamp(
                    psutil.boot_time()),
                "memory": psutil.virtual_memory().total,
            }
        }
