"""
Route URLs to correct resource handler.
"""

import logging
from aiohttp import web

logger = logging.getLogger('api')


class Router(object):

    def __init__(self, routes, default_exception_status=500,
                 default_exception_blur=False):
        self._routes = routes
        self._default_exception_status = default_exception_status
        self._default_exception_blur = default_exception_blur

    async def root(self, request):
        version, *pathing = request.match_info['path'].split('/')
        try:
            route = self._routes[version]
        except KeyError:
            route = self.directory
        return await route(request, pathing)

    async def __call__(self, request, pathing):
        try:
            route = self._routes[pathing[0]]
        except (KeyError, IndexError):
            route = self.directory
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
            logger.exception('Unhandled API Exception')
            if self._default_exception_blur:
                e_type = "general"
                e_msg = "error"
            else:
                e_type = type(e).__name__
                e_msg = str(e)
            return web.json_response({
                "exception": e_type,
                "message": e_msg
            }, status=self._default_exception_status)
        if isinstance(resp, web.Response):
            return resp
        else:
            return web.json_response(resp)

    async def directory(self, *_):
        return web.json_response(list(self._routes), status=404)


class Resource(object):
    """ Opinionated variant of a web.View.  A major difference between this
    class and a web.View is that you should pass an instance of this class
    to the server and not the class itself.  Any state that needs to travel
    with a request should live in the request object itself. """

    default_allowed_methods = {
        "GET"
    }

    def __init__(self, allowed_methods=default_allowed_methods):
        self._allowed_methods = set(map(str.upper, allowed_methods))

    async def __call__(self, request, pathing, **query):
        method = request.method
        if method not in self._allowed_methods or \
           not hasattr(self, method.lower()):
            raise web.HTTPMethodNotAllowed(method, self._allowed_methods)
        fn = getattr(self, method.lower())
        query = dict((key, request.GET.getall(key)) for key in request.GET)
        try:
            coro = fn(request, **query)
        except TypeError as e:
            raise web.HTTPBadRequest(text='Invalid query: %s' % str(e))
        return await coro
