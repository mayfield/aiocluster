
import aiocluster
import aiohttp.web
import asyncio
import itertools
import logging
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


loop = asyncio.get_event_loop()
logging.basicConfig(level=30)
counter = itertools.count()


def info(request):
    i = next(counter)
    if i % 1000 == 0:
        print(i)
    return aiohttp.web.Response(body=b'')


def child(ident, context):
    loop.create_task(server())
    loop.run_forever()


async def server():
    app = aiohttp.web.Application()
    await loop.create_server(app.make_handler(), '0.0.0.0', 8080,
                             reuse_port=True)
    app.router.add_route('GET', '/', info)


def parent():
    coord = aiocluster.Coordinator('simple_prefork_web:child',
                                   worker_count=4)
    loop.run_until_complete(coord.start())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()

if __name__ == '__main__':
    parent()
