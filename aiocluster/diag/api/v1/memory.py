"""
/api/v1/memory handler
"""

import asyncio
import logging
from aiohttp import web
from .... import coordinator

logger = logging.getLogger('api.v1.memory')


class MemoryView(web.View):

    def __init__(self, request, paths):
        self.paths = paths
        self.coord = coordinator.get_coordinator()
        super().__init__(request)

    async def get(self):
        req_type = self.request.GET.get('type', 'mostcommon')
        if req_type == 'mostcommon':
            batch = [x.rpc.call('memory_report')
                     for x in self.coord.workers.values()]
        elif req_type == 'growth':
            batch = [x.rpc.call('memory_growth')
                     for x in self.coord.workers.values()]
        else:
            raise web.HTTPBadRequest(text='Invalid type: %s' % req_type)
        return await asyncio.gather(*batch)
