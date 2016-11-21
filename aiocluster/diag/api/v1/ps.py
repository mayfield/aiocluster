"""
/api/v1/ps handler (process stats).
"""

import psutil
import time
from .. import util
from .... import coordinator


class PSResource(util.Resource):
    """ Process information. """

    use_docstring = True
    cproc = psutil.Process()
    cproc.cpu_percent()  # seed
    allowed_methods = {
        'GET',
        'KILL'
    }

    async def get(self, request):
        coord = coordinator.get_coordinator()
        workers = []
        now = time.time()
        for worker in coord.workers.values():
            ps = worker.util
            with ps.oneshot():
                workers.append({
                    "ident": worker.ident,
                    "age": now - ps.create_time(),
                    "pid": ps.pid,
                    "threads": ps.num_threads(),
                    "cpu_percent": ps.cpu_percent(),
                    "cpu_times": ps.cpu_times()._asdict(),
                    "memory": ps.memory_info()._asdict(),
                    "status": ps.status(),
                    "open_files": ps.num_fds()
                })
        with self.cproc.oneshot():
            return {
                "coordinator": {
                    "age": now - self.cproc.create_time(),
                    "pid": self.cproc.pid,
                    "threads": self.cproc.num_threads(),
                    "cpu_percent": self.cproc.cpu_percent(),
                    "cpu_times": self.cproc.cpu_times()._asdict(),
                    "memory": self.cproc.memory_info()._asdict(),
                    "status": self.cproc.status(),
                    "open_files": self.cproc.num_fds(),
                },
                "workers": workers
            }

    async def kill(self, request):
        """ Kill a worker process. """
        ident = await self.get_request_content(request)
        coord = coordinator.get_coordinator()
        if ident not in coord.workers:
            raise ValueError("Invalid worker ident: %r" % ident)
        worker = coord.workers[ident]
        worker.util.terminate()
