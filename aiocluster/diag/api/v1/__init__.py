"""
Route URLs to correct resource handler.
"""

import logging
from aiohttp import web
from . import profiler

logger = logging.getLogger('diag.api.v1')

routes = {
    'profiler': profiler.ProfilerView
}


async def router(request, pathing):
    try:
        route = routes[pathing[0]]
    except (KeyError, IndexError):
        route = directory
    try:
        resp = await route(request, pathing[1:])
    except web.HTTPError as e:
        return web.json_response({
            "exception": type(e).__name__,
            "message": e.text
        }, status=e.status)
    except web.HTTPException:
        raise  # Let HTTPError > e <= HTTPException slip through
    except Exception as e:
        e_type = type(e).__name__
        e_msg = str(e)
        logger.exception('Unhandled API Exception: %s(%s)' % (e_type, e_msg))
        return web.json_response({
            "exception": e_type,
            "message": e_msg
        }, status=500)
    else:
        if isinstance(resp, web.Response):
            return resp
        else:
            return web.json_response(resp)


async def directory(request, _):
    return web.json_response(list(routes), status=404)
