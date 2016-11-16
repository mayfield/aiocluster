"""
/api/v1/about handler for info about this execution of aiocluster.
"""

import asyncio
import platform
from .. import util
from .... import coordinator


class AboutResource(util.Resource):

    async def get(self, request):
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
            "platform": {
                "system": platform.system(),
                "machine": platform.machine(),
                "python_implementation": platform.python_implementation(),
                "python_version": platform.python_version(),
            }
        }
