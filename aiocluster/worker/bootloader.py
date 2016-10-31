"""
This module should only ever be used by the spawn() routine.
"""

import asyncio
import datetime
import logging
import os
import shellish
import time
from . import env, service
from .. import setup

logger = logging.getLogger('worker.bootloader')


class Launcher(shellish.Command):
    """ AIOCluster launcher [Internal use only]

    This is called by worker.spawn() to load a new python process who
    shares some context and identity with the parent without using a
    fork-without-exec pattern.  Context is passed through the temporary env
    variable that is purged on startup to avoid blatantly sharing secrets. """

    worker_spec_help = 'The worker_spec should be in the form of ' \
        '`module.submodule:coro_or_service`.  The function must accept 1 ' \
        'positional args for a `worker_service` instance.'
    ident_help = 'Numeric identifier of worker process.'

    def setup_args(self, parser):
        self.add_argument('worker_spec', help=self.worker_spec_help)
        self.add_argument('ident', type=int, help=self.ident_help)

    def setup(self, error_verbosity=None, logging=None, event_loop=None,
              mixins=None):
        """ Perform early setup. """
        if error_verbosity is not None:
            self.session.command_error_verbosity = error_verbosity
        if logging is not None:
            setup.setup_logging(**logging)
        if event_loop is None:
            event_loop = {}
        self._worker_mixins = []
        if mixins:
            for x in mixins:
                logger.debug("Adding WorkerService mixin: %s" % x)
                self._worker_mixins.append(service.mixins[x])
        self._loop = setup.get_event_loop(**event_loop)

    def run(self, args):
        """ Extract configuration from the shell ENV.  Then run a
        WorkerService forever. """
        start = time.monotonic()
        bootenv = env.decode(os.environ.pop('_AIOCLUSTER_BOOTLOADER'))
        self.setup(**bootenv['settings'])
        thing = setup.find_worker(args.worker_spec)
        ws = self.make_worker_service(thing, args.ident, bootenv['context'],
                                      loop=self._loop,
                                      run_args=bootenv['args'],
                                      run_kwargs=bootenv['kwargs'])
        try:
            self._loop.run_until_complete(ws())
        finally:
            uptime = round(time.monotonic() - start)
            logger.warning('Worker exited after %s' %
                           datetime.timedelta(seconds=uptime))
            self._loop.close()

    def make_worker_service(self, worker_thing, *ws_args, **ws_kwargs):
        """ Inspect a worker "thing" and return a WorkerService instance
        appropriate for the type of worker_thing. """
        if isinstance(worker_thing, type) and \
           issubclass(worker_thing, service.WorkerService):
            logger.debug("Detected WorkerService worker: %s" % worker_thing)
            worker_base_class = worker_thing
            run = None
        elif callable(worker_thing):
            worker_base_class = service.WorkerService
            if asyncio.iscoroutinefunction(worker_thing):
                logger.debug("Detected coroutine worker: %s" % worker_thing)
                run = worker_thing
            else:
                logger.debug("Detected function worker: %s" % worker_thing)
                async def c(*args, **kwargs):
                    return worker_thing(*args, **kwargs)
                run = c
        else:
            raise TypeError('Worker must be a coroutine, function or '
                            'subclass of WorkerService.')
        worker_bases = tuple(self._worker_mixins) + (worker_base_class,)
        worker_class = type('FinalizedWorkerService', worker_bases, {})
        return worker_class(*ws_args, run=run, **ws_kwargs)


if __name__ == '__main__':
    Launcher()()
else:
    raise ImportError("Do not use bootloader module directly")
