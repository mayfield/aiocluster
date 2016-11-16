"""
Diagnostic service (with web ui) that runs in the coordinator.
"""

import logging
import os
import platform
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
        for x in ('/', '/ui', '/ui/'):
            self._app.router.add_route('GET', x, self.about_redir)
        self._app.router.add_route('GET', '/health', self.health)
        self._app.router.add_route('GET', '/api', api.router.directory)
        self._app.router.add_route('*', '/api/{path:.*}', api.router.root)
        self._app.router.add_static('/ui', self.ui_dir)
        self._handler = self._app.make_handler()
        listen = self.addr, self.port
        self._server = await self._loop.create_server(self._handler, *listen)
        logger.info('Diag web server running: http://%s:%s' % listen)

    async def about_redir(self, request):
        return web.HTTPFound('/ui/about.html')

    async def health(self, request):
        # XXX/TODO Create thresholds for mem usage and possibly cpu usage to
        # use in determining health pass/fail.
        # TODO: Add registry for user code to register health tests.
        # Eg. diag_service.add_health_test(my_callback)
        # Where my callback can trigger an unhealthy response with either a
        # falsy value or an exception.
        return web.json_response({
            "platform_info": self.platform_info,
        })

    async def stop(self):
        self._coordinator = None
        self._server.close()
        await self._server.wait_closed()
        await self._app.shutdown()
        await self._handler.finish_connections(1)
        await self._app.cleanup()
