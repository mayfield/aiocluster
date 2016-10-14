"""
/api/v1/profiler handler
"""

import asyncio
import logging
from aiohttp import web
from .... import coordinator

logger = logging.getLogger('diag.v1.profiler')


class ProfilerView(web.View):

    actions = [
        'stop',
        'start',
        'report'
    ]

    def __init__(self, request, paths):
        self.paths = paths
        self.coord = coordinator.get_coordinator()
        super().__init__(request)

    async def get(self):
        if len(self.paths) != 1 or self.paths[0] not in self.actions:
            return web.json_response(['stop', 'start', 'report'], status=404)
        action = self.paths[0]
        if action != 'report':
            raise web.HTTPMethodNotAllowed('get', ['put'])
        return await self.report()

    async def report(self):
        batch = [x.rpc.call('report_profiler')
                 for x in self.coord.workers.values()]
        return await asyncio.gather(*batch)

    async def put(self):
        if len(self.paths) != 1 or self.paths[0] not in self.actions:
            return web.json_response(['stop', 'start', 'report'], status=404)
        action = self.paths[0]
        if action == 'report':
            raise web.HTTPMethodNotAllowed('put', ['get'])
        workers = self.coord.workers.values()
        if self.request.content_length:
            try:
                args = await self.request.json()
            except ValueError as e:
                raise  web.HTTPBadRequest(text='Invalid JSON: %s' % e)
            worker = args.get('worker')
            if worker is not None:
                try:
                    workers = [self.coord.workers[worker]]
                except KeyError:
                    raise  web.HTTPBadRequest(text='Missing/Invalid `worker`')
        call = '%s_profiler' % action
        batch = [x.rpc.call(call) for x in workers]
        return await asyncio.gather(*batch)
