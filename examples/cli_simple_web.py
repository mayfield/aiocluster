"""
To run `aiocluster simple_prefork_web:worker`
"""

import aiohttp.web
import asyncio
import itertools

loop = asyncio.get_event_loop()
counter = itertools.count()


def info(request):
    return aiohttp.web.Response(body=b'%d' % next(counter))


async def server():
    app = aiohttp.web.Application()
    await loop.create_server(app.make_handler(), '0.0.0.0', 8080,
                             reuse_port=True)
    app.router.add_route('GET', '/', info)


def worker(ident, context):
    loop.create_task(server())
    loop.run_forever()
