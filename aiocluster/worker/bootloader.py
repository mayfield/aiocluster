"""
This module should only ever be used by the spawn() routine.
"""

import argparse
import datetime
import logging
import os
import shellish
import time
from . import env
from .. import setup

logger = logging.getLogger('worker.bootloader')


class Launcher(shellish.Command):
    """ Worker launcher [Internal use only]

    This is called by worker.spawn() to load a new python process who
    shares some context and identity with the parent without using a
    fork-without-exec pattern.  Context is passed through the temporary env
    variable that is purged on startup to avoid blatantly sharing secrets. """

    name = 'launcher'

    def setup_args(self, parser):
        self.add_argument('worker_spec')
        self.add_argument('ident', type=int)

    def run(self, args):
        """ Extract configuration from the shell ENV.  Then run the appropriate
        WorkerCommand. """
        bootenv = env.decode(os.environ.pop('_AIOCLUSTER_BOOTLOADER'))
        settings = bootenv['settings'] or {}
        setup.setup_logging(**settings.get('logging', {}))
        loop = setup.get_event_loop(**settings.get('event_loop', {}))
        WorkerCmd = setup.worker_coerce(setup.find_worker(args.worker_spec))
        worker_cmd = WorkerCmd(ident=args.ident, config=bootenv['config'],
                               loop=loop)
        if settings.get('error_verbosity') is not None:
            session = worker_cmd.get_or_create_session()
            session.command_error_verbosity = settings['error_verbosity']
        start = time.monotonic()
        try:
            worker_cmd(args=argparse.Namespace(**(bootenv['args'] or {})))
        finally:
            uptime = round(time.monotonic() - start)
            logger.warning('Worker exited after %s' %
                           datetime.timedelta(seconds=uptime))
            loop.close()


if __name__ == '__main__':
    Launcher()()
else:
    raise ImportError("Do not use bootloader module directly")
