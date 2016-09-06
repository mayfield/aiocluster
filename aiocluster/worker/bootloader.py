"""
This module should only ever be used by the spawn() routine.
"""

import importlib
import logging
import os
import shellish
from . import env

logger = logging.getLogger('worker.bootloader')


class Launcher(shellish.Command):
    """ AIOCluster launcher [Internal use only]

    This is called by worker.spawn() to load a new python process who
    shares some context and identity with the parent without using a
    fork-without-exec pattern.  Context is passed through the temporary env
    variable that is purged on startup to avoid blatantly sharing secrets. """

    worker_spec_help = 'The worker_spec should be in the form of ' \
        '`module.submodule:function_name`.  The function must accept 2 ' \
        'positional args for `ident` and `context` respectively.'
    ident_help = 'Numeric or string identifier of worker process.'

    def setup_args(self, parser):
        self.add_argument('worker_spec', help=self.worker_spec_help)
        self.add_argument('ident', help=self.ident_help)
        verbosity = {'traceback', 'pretty', 'debug', 'raise'}
        self.add_argument('--error-verbosity', choices=verbosity,
                          default='traceback')

    def run(self, args):
        self.session.command_error_verbosity = args.error_verbosity
        setup = env.decode(os.environ.pop('_AIOCLUSTER_BOOTLOADER'))
        module, func = args.worker_spec.split(':', 1)
        module = importlib.import_module(module)
        fn = getattr(module, func)
        fn(args.ident, setup['context'], *setup['args'], **setup['kwargs'])


if __name__ == '__main__':
    Launcher()()
else:
    raise ImportError("Do not use bootloader module directly")
