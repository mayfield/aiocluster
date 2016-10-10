"""
Command line interface for interacting with an aiocluster service.
"""

import os.path
import requests
import shellish


class AIOClusterControl(shellish.Command):
    """ Control operations for an AIO Cluster service. """

    name = 'aiocluster-control'

    def setup_args(self, parser):
        self.add_argument('--url', default='http://127.0.0.1:7878',
                          autoenv=True, help='URL to connect to.')
        self.add_subcommand(Profiler)


class Profiler(shellish.Command):

    name = 'profiler'

    def setup_args(self, parser):
        self.add_subcommand(StartProfiler)
        self.add_subcommand(StopProfiler)
        self.add_subcommand(ReportProfiler)


class ProfilerMixin(object):

    urn = '/api/v1/profiler'
    def setup_args(self, parser):
        self.add_argument('--worker', type=int, default=0)
        super().setup_args(parser)


class StartProfiler(ProfilerMixin, shellish.Command):

    name = 'start'

    def run(self, args):
        requests.put(args.url + self.urn, json={
            "worker": args.worker,
            "action": "start"
        })


class StopProfiler(ProfilerMixin, shellish.Command):

    name = 'stop'

    def run(self, args):
        requests.put(args.url + self.urn, json={
            "worker": args.worker,
            "action": "stop"
        })


class ReportProfiler(ProfilerMixin, shellish.Command):

    name = 'report'
    use_pager = True

    def setup_args(self, parser):
        self.add_argument('--sortby', choices=('cumulative', 'total', 'calls'),
                          default='cumulative')
        super().setup_args(parser)

    def run(self, args):
        stats = requests.put(args.url + self.urn, json={
            "worker": args.worker,
            "action": "report"
        }).json()
        stats.sort(key=lambda x: x['stats'][args.sortby], reverse=True)
        table = shellish.Table(columns=[
            None,
            None,
            {"minwidth": 4},
            {"minwidth": 8},
            {"minwidth": 8},
            {"minwidth": 8},
        ], headers=[
            'Function',
            'File',
            'Line #',
            'Cumulative',
            'Total',
            'Calls'
        ])
        table.print([
            x['call']['function'],
            os.path.basename(x['call']['file']),
            x['call']['lineno'],
            '%f' % x['stats']['cumulative'],
            '%f' % x['stats']['total'],
            x['stats']['calls']
        ] for x in stats)


def entry():
    AIOClusterControl()()
