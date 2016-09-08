"""
To run `python3 ./simple_web.py`
"""

import aiocluster
import aiohttp.web
import asyncio
import itertools
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()
counter = itertools.count()


def info(request):
    return aiohttp.web.Response(body=b'%d' % next(counter))


def child(ident, context):
    loop.create_task(server())
    loop.run_forever()


async def server():
    app = aiohttp.web.Application()
    await loop.create_server(app.make_handler(), '0.0.0.0', 8080,
                             reuse_port=True)
    app.router.add_route('GET', '/', info)


def parent():
    coord = aiocluster.Coordinator('simple_web:child', worker_count=6)
    loop.run_until_complete(coord.start())
    loop.run_forever()

if __name__ == '__main__':
    parent()
