"""
Command line interface for interacting with an aiocluster service.
"""

import shellish
from . import profiler, memory


class AIOClusterControl(shellish.Command):
    """ Control operations for an AIO Cluster service. """

    name = 'aiocluster-control'

    def setup_args(self, parser):
        self.add_argument('--url', default='http://127.0.0.1:7878',
                          autoenv=True, help='URL to connect to.')
        self.add_subcommand(profiler.Profiler)
        self.add_subcommand(memory.Memory)


def entry():
    AIOClusterControl()()
