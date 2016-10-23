"""
Memory stats
"""

import collections
import requests
import shellish


class Memory(shellish.Command):

    name = 'memory'

    def setup_args(self, parser):
        self.add_subcommand(Show, default=True)


class MemoryMixin(object):

    urn = '/api/v1/memory/'


class Show(MemoryMixin, shellish.Command):

    name = 'show'
    use_pager = True

    def setup_args(self, parser):
        self.add_argument('--type', choices=('mostcommon', 'growth'),
                          default='mostcommon')

    def run(self, args):
        report = requests.get(args.url + self.urn, params=dict(type=args.type))
        if not report.ok:
            print(report.json())
            return
        if args.type == 'growth':
            return self.show_growth(report.json())
        else:
            return self.show_mostcommon(report.json())

    def show_mostcommon(self, report):
        merged = collections.defaultdict(lambda: 0)
        for worker in report:
            for otype, count in worker:
                merged[otype] += count
        stats = sorted(merged.items(), key=lambda x: x[1], reverse=True)
        table = shellish.Table(headers=[
            'Type',
            'Count',
        ])
        table.print(stats)

    def show_growth(self, report):
        merged = collections.defaultdict(lambda: [0, 0])
        for worker in report:
            for otype, count, change in worker:
                merged[otype][0] += count
                merged[otype][1] += change
        stats = sorted(((k, *v) for k, v in merged.items()),
                        key=lambda x: x[2], reverse=True)
        table = shellish.Table(headers=[
            'Type',
            'Count',
            'Change',
        ])
        table.print(stats)
