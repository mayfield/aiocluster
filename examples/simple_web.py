"""
To run `python3 ./simple_web.py`
"""

import aiocluster
import aiohttp.web
import asyncio
import itertools

loop = asyncio.get_event_loop()
counter = itertools.count()


def info(request):
    return aiohttp.web.Response(body=b'%d' % next(counter))


async def worker(ident, context):
    app = aiohttp.web.Application()
    server = await loop.create_server(app.make_handler(), '0.0.0.0', 8080,
                                      reuse_port=True)
    app.router.add_route('GET', '/', info)
    print("Server running: http://localhost:8080")
    await server.wait_closed()


def parent():
    coord = aiocluster.Coordinator('simple_web:worker')
    loop.run_until_complete(coord.start())
    try:
        loop.run_until_complete(coord.wait_stopped())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(coord.stop())
        loop.close()

if __name__ == '__main__':
    parent()
