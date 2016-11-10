"""
Command line interface for managing an aiocluster service.
"""

import pkg_resources
import shellish
from . import run, control


class RootCommand(shellish.Command):
    """ Root command for aiocluster operations.

    Most behvior is in the subcommands of this tool. """

    name = 'aiocluster'

    def setup_args(self, parser):
        version = pkg_resources.require("aiocluster")[0].version
        self.add_argument('--version', action='version', version=version)
        self.add_subcommand(run.RunCommand)
        self.add_subcommand(control.ControlCommand)


def main():
    RootCommand()()
