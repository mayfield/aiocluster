"""
Route API calls to correct sub handlers.
"""

from aiohttp import web
from . import v1

routes = {
    'v1': v1.router
}


async def router(request):
    version, *pathing = request.match_info['path'].split('/')
    try:
        route = routes[version]
    except KeyError:
        route = directory
    return await route(request, pathing)


async def directory(request, *_):
    return web.json_response(list(routes), status=404)
