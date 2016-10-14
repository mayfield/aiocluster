"""
Diagnostic service (with web ui) that runs in the coordinator.
"""

import logging
import os
import platform
import psutil
from . import api
from aiohttp import web

logger = logging.getLogger('diag')


class DiagService(object):
    """ Diagnostic Web Service. """

    platform_info = {
        "system": platform.system(),
        "platform": platform.platform(),
        "node": platform.node(),
        "dist": ' '.join(platform.dist()),
        "python": platform.python_version()
    }
    ui_dir = os.path.join(os.path.dirname(__file__), 'ui')

    def __init__(self, addr=None, port=None, coordinator=None, loop=None):
        self.addr = addr
        self.port = port
        self._coordinator = coordinator
        self._loop = loop

    async def start(self):
        self._app = web.Application(loop=self._loop)
        self._app.router.add_route('GET', '/', self.index_redir)
        self._app.router.add_route('GET', '/health', self.health)
        self._app.router.add_route('GET', '/api', api.directory)
        self._app.router.add_route('*', '/api/{path:.*}', api.router)
        self._app.router.add_static('/ui', self.ui_dir)
        self._handler = self._app.make_handler()
        listen = self.addr, self.port
        self._server = await self._loop.create_server(self._handler, *listen)
        logger.info('Diag web server running: http://%s:%s' % listen)

    async def index_redir(self, request):
        return web.HTTPFound('/ui/index.html')

    async def health(self, request):
        coord_proc = psutil.Process()
        return web.json_response({
            "platform_info": self.platform_info,
            "coordinator": {
                "pid": coord_proc.pid,
                "cpu_times": coord_proc.cpu_times()._asdict(),
                "memory": coord_proc.memory_info()._asdict()
            },
            "workers": [{
                "ident": x.ident,
                "age": x.age().total_seconds(),
                "pid": x.util.pid,
                "threads": x.util.num_threads(),
                "connections": len(x.util.connections()),
                "cpu_percent": x.util.cpu_percent(),
                "cpu_times": x.util.cpu_times()._asdict(),
                "memory": x.util.memory_info()._asdict(),
                "status": x.util.status(),
            } for x in self._coordinator.workers.values()]
        })

    async def stop(self):
        self._coordinator = None
        self._server.close()
        await self._server.wait_closed()
        await self._app.shutdown()
        await self._handler.finish_connections(1)
        await self._app.cleanup()
