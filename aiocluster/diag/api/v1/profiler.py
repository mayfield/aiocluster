"""
/api/v1/profiler handler
"""

import asyncio
import logging
from .. import util
from .... import coordinator
from aiohttp import web

logger = logging.getLogger('api.v1.profiler')


class ActiveResource(util.Resource):
    """ View and control the profiler state. """

    use_docstring = True
    allowed_methods = {
        'GET',
        'PUT'
    }

    async def put(self, request):
        active = await self.get_request_content(request)
        if not isinstance(active, bool):
            raise  web.HTTPBadRequest(text='Bool type expected')
        workers = coordinator.get_coordinator().workers.values()
        batch = [x.rpc.call('profiler_set_active', active) for x in workers]
        return await asyncio.gather(*batch)

    async def get(self, request):
        workers = coordinator.get_coordinator().workers.values()
        batch = [x.rpc.call('profiler_get_active') for x in workers]
        return await asyncio.gather(*batch)


class ReportResource(util.Resource):
    """ Gather profiler stats from all workers. """

    use_docstring = True

    async def get(self, request):
        workers = coordinator.get_coordinator().workers.values()
        batch = [x.rpc.call('profiler_report') for x in workers]
        return await asyncio.gather(*batch)


ProfilerRouter = util.Router({
    'active': ActiveResource(),
    'report': ReportResource(),
}, desc="Profiler endpoints.")

