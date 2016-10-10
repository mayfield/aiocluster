"""
To run `aiocluster cli_simple_web:worker`
"""

import aiohttp.web
import asyncio
import itertools
import logging

loop = asyncio.get_event_loop()
counter = itertools.count()
logger = logging.getLogger('cli_simple_web')


def info(request):
    return aiohttp.web.Response(body=b'%d' % next(counter))


async def worker(s):
    app = aiohttp.web.Application()
    server = await loop.create_server(app.make_handler(), '0.0.0.0', 8080,
                                      reuse_port=True)
    app.router.add_route('GET', '/', info)
    await server.wait_closed()
