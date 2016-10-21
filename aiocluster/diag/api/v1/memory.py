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
        batch = [x.rpc.call('memory_report')
                 for x in self.coord.workers.values()]
        return await asyncio.gather(*batch)
