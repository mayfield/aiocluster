"""
Command line interface for interacting with an aiocluster service.
"""

import requests
import shellish
import logging
from .. import coordinator, setup

logger = logging.getLogger('cli.aiocluster.control')


class AIOClusterControl(shellish.Command):
    """ Control operations for an AIO Cluster service. """

    name = 'aiocluster-control'

    def setup_args(self, parser):
        self.add_argument('--url', default='http://127.0.0.1:7878',
                          autoenv=True, help='URL to connect to.')
        self.add_subcommand(Profiler)


class Profiler(shellish.Command):

    name = 'profiler'
    urn = '/api/v1/profiler'

    def setup_args(self, parser):
        self.add_subcommand(StartProfiler)
        self.add_subcommand(StopProfiler)



class StartProfiler(shellish.Command):

    name = 'start'

    def setup_args(self, parser):
        self.add_argument('--worker', type=int, default=0)

    def run(self, args):
        requests.put(args.url + self.urn, data={
            "worker": args.worker,
            "action": "start"
        })

class StopProfiler(shellish.Command):

    name = 'stop'

    def run(self, args):
        resp = requests.put(args.url + self.urn, data={
            "worker": args.worker,
            "action": "stop"
        }).json()
        t = shellish.Table(headers=['File', 'Func')


def entry():
    AIOClusterControl()()
