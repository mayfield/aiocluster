"""
Route URLs to correct resource handler.
"""

import contextlib
import inspect
import logging
from aiohttp import web

logger = logging.getLogger('api')


class AbstractRoute(object):
    """ Shared by router and resource for common handling. """

    allowed_methods = set()
    default_exception_status = 500
    default_exception_blur = False  # show/hide from API output
    use_docstring = False
    desc = None

    def __init__(self, desc=None, use_docstring=None, allowed_methods=None,
                 default_exception_status=None, default_exception_blur=None):
        if desc is not None:
            self.desc = desc
        else:
            if use_docstring is None:
                use_docstring = self.use_docstring
            if use_docstring:
                self.desc = inspect.getdoc(self).strip()
        if allowed_methods is not None:
            self.allowed_methods = allowed_methods
        if default_exception_status is not None:
            self.default_exception_status = default_exception_status
        if default_exception_blur is not None:
            self.default_exception_blur = default_exception_blur
        super().__init__()

    def check_request(self, request):
        """ Assert that the method being attempted is valid. """
        method = request.method
        if not ({method, '*'} & self.allowed_methods):
            raise web.HTTPMethodNotAllowed(method, self.allowed_methods)

    async def __call__(self, request, *args, **kwargs):
        self.check_request(request)
        return await self.handler(request, *args, **kwargs)

    async def handler(self, *args, **kwargs):
        raise NotImplementedError("Required subclass impl")

    @contextlib.contextmanager
    def exception_filter(self):
        """ Format exceptions into API consumable formats. """
        try:
            yield
        except web.HTTPError as e:
            raise web.json_response({
                "exception": type(e).__name__,
                "message": e.text
            }, status=e.status)
        except web.HTTPException:
            raise  # Let HTTPError > e <= HTTPException slip through
        except Exception as e:
            logger.exception('Unhandled API Exception')
            if self.default_exception_blur:
                e_type = "general"
                e_msg = "error"
            else:
                e_type = type(e).__name__
                e_msg = str(e)
            return web.json_response({
                "exception": e_type,
                "message": e_msg
            }, status=self.default_exception_status)


class Router(AbstractRoute):
    """ Redirect traffic to another route or resource. """

    allowed_methods = {
        '*'
    }

    def __init__(self, routes, **kwargs):
        self._routes = routes
        super().__init__(**kwargs)

    def attach(self, app, urn):
        """ Use this in your aiohttp application to attach this router to a
        base URN.  The URN should not end in slash. Eg. `/api`. """
        assert not urn.endswith('/'), "urn should not end with a `/`"

        async def redirect(request):
            return web.HTTPFound('%s/' % urn)
        app.router.add_route('*', urn, redirect)
        app.router.add_route('*', '%s/{path:.*}' % urn, self.hook)

    async def hook(self, request):
        """ TODO: Support direct hook of Resource too and move to Abstract. """
        try:
            res, *pathing = request.match_info['path'].split('/')
            try:
                route = self._routes[res]
            except KeyError:
                return self.directory()
            return await route(request, pathing)
        except web.HTTPException as e:
            return web.json_response({
                "exception": type(e).__name__,
                "message": e.text
            }, status=e.status)
        except Exception as e:
            logger.exception('Unhandled API Exception')
            if self.default_exception_blur:
                e_type = "general"
                e_msg = "error"
            else:
                e_type = type(e).__name__
                e_msg = str(e)
            return web.json_response({
                "exception": e_type,
                "message": e_msg
            }, status=self.default_exception_status)

    async def handler(self, request, pathing):
        try:
            route = self._routes[pathing[0]]
        except (KeyError, IndexError):
            return self.directory()
        resp = await route(request, pathing[1:])
        if isinstance(resp, web.Response):
            return resp
        else:
            return web.json_response(resp)

    def directory(self):
        return web.json_response(dict(choices=[{
            "endpoint": ep,
            "desc": route.desc,
            "allowed_methods": tuple(route.allowed_methods)
        } for ep, route in self._routes.items()]), status=404)


class Resource(AbstractRoute):
    """ Opinionated variant of a web.View.  A major difference between this
    class and a web.View is that you should pass an instance of this class
    to the server and not the class itself.  Any state that needs to travel
    with a request should live in the request object itself. """

    allowed_methods = {
        "GET"
    }

    def check_request(self, request):
        """ Add additional check for method implementation. """
        super().check_request(request)
        method = request.method
        if not hasattr(self, method.lower()):
            raise web.HTTPNotImplemented('Missing implementation: %s' % method)

    async def handler(self, request, pathing, **query):
        fn = getattr(self, request.method.lower())
        query = dict((key, request.GET.getall(key)) for key in request.GET)
        try:
            coro = fn(request, **query)
        except TypeError as e:
            raise web.HTTPBadRequest(text='Invalid query: %s' % str(e))
        return await coro

    async def get_request_content(self, request):
        """ Read JSON content from a request content body and return a proper
        HTTP error if the value is invalid. """
        try:
            return await request.json()
        except ValueError as e:
            raise  web.HTTPBadRequest(text='Invalid JSON Content: %s' % e)
