"""
/api/v1/ps handler (process stats).
"""

import psutil
from .. import util
from .... import coordinator


class PSResource(util.Resource):

    async def get(self, request):
        coord = coordinator.get_coordinator()
        coord_util = psutil.Process()
        return {
            "coordinator": {
                "pid": coord_util.pid,
                "cpu_times": coord_util.cpu_times()._asdict(),
                "memory": coord_util.memory_info()._asdict(),
                "cpu_percent": coord_util.cpu_percent(),
            },
            "workers": [{
                "ident": x.ident,
                "age": x.age().total_seconds(),
                "pid": x.util.pid,
                "threads": x.util.num_threads(),
                "cpu_percent": x.util.cpu_percent(),
                "cpu_times": x.util.cpu_times()._asdict(),
                "memory": x.util.memory_info()._asdict(),
                "status": x.util.status(),
            } for x in coord.workers.values()]
        }
