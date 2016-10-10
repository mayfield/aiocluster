"""
This module should only ever be used by the spawn() routine.
"""

import asyncio
import datetime
import importlib
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

    def run(self, args):
        self.start = time.monotonic()
        bootenv = env.decode(os.environ.pop('_AIOCLUSTER_BOOTLOADER'))
        self.setup(**bootenv['settings'])
        module, funcpath = args.worker_spec.split(':', 1)
        module = importlib.import_module(module)
        offt = module
        for x in funcpath.split('.'):
            offt = getattr(offt, x)
        fn = offt
        self.run_worker(fn, self.loop, args.ident, bootenv['context'],
                        *bootenv['args'], **bootenv['kwargs'])

    def setup(self, error_verbosity=None, logging=None, event_loop=None):
        """ Perform early setup. """
        if error_verbosity is not None:
            self.session.command_error_verbosity = error_verbosity
        if logging is not None:
            setup.setup_logging(**logging)
        if event_loop is None:
            event_loop = {}
        self.loop = setup.get_event_loop(**event_loop)

    def run_worker(self, worker_fn, loop, *args, **kwargs):
        """ Run and wait (forever) on worker coro or WorkerService class. """
        if asyncio.iscoroutinefunction(worker_fn):
            worker = service.WorkerService(*args, run=worker_fn, **kwargs)
        elif issubclass(worker_fn, service.WorkerService):
            worker = worker_fn(*args, **kwargs)
        else:
            raise TypeError('worker function must be a coroutine or '
                            'WorkerService subclass')
        try:
            loop.run_until_complete(worker())
        finally:
            uptime = round(time.monotonic() - self.start)
            logger.warning('Worker exited after %s' %
                           datetime.timedelta(seconds=uptime))
            loop.close()


if __name__ == '__main__':
    Launcher()()
else:
    raise ImportError("Do not use bootloader module directly")
