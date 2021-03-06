"""
Command line interface for interacting with an active aiocluster service.
"""

import shellish
from . import profiler, memory


class DiagCommand(shellish.Command):
    """ Diagnostic operations for an AIO Cluster service. """

    name = 'diag'

    def setup_args(self, parser):
        self.add_argument('--url', default='http://127.0.0.1:7878',
                          autoenv=True, help='URL to connect to.')
        self.add_subcommand(profiler.Profiler)
        self.add_subcommand(memory.Memory)
