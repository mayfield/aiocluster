"""
Diagnostic service (with web ui) that runs in the coordinator.
"""

import aiohttp_jinja2
import datetime
import jinja2
import logging
import os
import platform
from .. import service
from aiohttp import web

logger = logging.getLogger('diag')


class DiagService(service.AIOService):
    """ Diagnostic Web Service. """

    platform_info = {
        "system": platform.system(),
        "platform": platform.platform(),
        "node": platform.node(),
        "dist": ' '.join(platform.dist()),
        "python": platform.python_version()
    }
    ui_dir = os.path.join(os.path.dirname(__file__), 'ui')

    def __init__(self, addr=None, port=None, **kwargs):
        super().__init__(**kwargs)
        self.addr = addr
        self.port = port
        self.tpl_context = self.context.copy()
        self.tpl_context.update({
            "environ": os.environ,
            "platform": self.platform_info,
            "ui_dir": self.ui_dir,
            "started": datetime.datetime.now(),
        })

    async def start(self):
        self.app = web.Application(loop=self.loop)
        tpl_loader = jinja2.FileSystemLoader(self.ui_dir)
        env = aiohttp_jinja2.setup(self.app, loader=tpl_loader)
        env.globals.update({
            "sorted": sorted
        })
        self.app.router.add_route('GET', '/', self.index_redir)
        self.app.router.add_route('GET', '/health', self.health)
        self.app.router.add_route('GET', '/ui/{path}', self.tpl_handler)
        self.app.router.add_static('/ui/static',
                                   os.path.join(self.ui_dir, 'static'))
        self.handler = self.app.make_handler()
        print(self.context)
        listen = self.addr, self.port
        self.server = await self.loop.create_server(self.handler, *listen)
        logger.info('Diag web server running: http://%s:%s' % listen)

    async def index_redir(self, request):
        return web.HTTPFound('/ui/index.html')

    async def health(self, request):
        return web.json_response({
            "platform_info": self.platform_info,
            "tasks": [x.cmd for x in self.tasks],
        })

    async def tpl_handler(self, request):
        path = request.match_info['path']
        context = self.tpl_context.copy()
        context['request'] = request
        return aiohttp_jinja2.render_template(path, request, context)

    async def stop(self):
        self.server.close()
        await self.server.wait_closed()
        await self.app.shutdown()
        await self.handler.finish_connections(1)
        await self.app.cleanup()
