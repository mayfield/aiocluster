"""
/api/v1/memory handler
"""

import asyncio
from aiohttp import web
from .. import util
from .... import coordinator


class MemoryResource(util.Resource):

    @property
    def coord(self):
        try:
            return self._coord
        except AttributeError:
            self._coord = coordinator.get_coordinator()
            return self._coord

    async def get(self, request, type=['mostcommon']):
        type = type[0]
        if type == 'mostcommon':
            batch = [x.rpc.call('memory_report')
                     for x in self.coord.workers.values()]
        elif type == 'growth':
            batch = [x.rpc.call('memory_growth')
                     for x in self.coord.workers.values()]
        else:
            raise web.HTTPBadRequest(text='Invalid type: %s' % type)
        return await asyncio.gather(*batch)
