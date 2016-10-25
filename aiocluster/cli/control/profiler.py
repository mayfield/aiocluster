"""
Command line interface for interacting with an aiocluster service.
"""

import requests
import shellish
import shutil
import time


class Profiler(shellish.Command):

    name = 'profiler'

    def setup_args(self, parser):
        self.add_subcommand(Start)
        self.add_subcommand(Stop)
        self.add_subcommand(Report)
        self.add_subcommand(Top)


class ProfilerMixin(object):

    urn = '/api/v1/profiler/'


class Start(ProfilerMixin, shellish.Command):

    name = 'start'

    def run(self, args):
        print(requests.put(args.url + self.urn + 'start'))


class Stop(ProfilerMixin, shellish.Command):

    name = 'stop'

    def run(self, args):
        requests.put(args.url + self.urn + 'stop')


class Report(ProfilerMixin, shellish.Command):

    name = 'report'
    use_pager = True

    def setup_args(self, parser):
        self.add_argument('--sortby', choices=('totaltime', 'inlinetime',
                          'callcount'), default='totaltime')
        self.add_argument('--limit', type=int, default=None)

    def run(self, args):
        report = requests.get(args.url + self.urn + 'report')
        if not report.ok:
            print(report.json())
            return
        by_call = {}
        for stats in report.json():
            for x in stats:
                key = (
                    x['call']['file'],
                    x['call']['function'],
                    x['call']['lineno']
                )
                try:
                    ref = by_call[key]
                except KeyError:
                    by_call[key] = x['stats']
                else:
                    ref['totaltime'] += x['stats']['totaltime']
                    ref['inlinetime'] += x['stats']['inlinetime']
                    ref['callcount'] += x['stats']['callcount']
        stats = sorted(by_call.items(), key=lambda x: x[1][args.sortby],
                       reverse=True)
        table = shellish.Table(headers=[
            'Function',
            'Total Time',
            'Inline Time',
            'Calls'
        ])
        if args.limit is not None:
            del stats[args.limit:]
        table.print([
            '%s:%s:%s' % ('/'.join(x[0][0].rsplit('/', 2)[-2:]), x[0][1],
                          x[0][2]),
            '%f' % x[1]['totaltime'],
            '%f' % x[1]['inlinetime'],
            x[1]['callcount']
        ] for x in stats)


class Top(ProfilerMixin, shellish.Command):

    name = 'top'
    use_pager = False

    def setup_args(self, parser):
        self.add_argument('--sortby', choices=('totaltime', 'inlinetime',
                          'callcount'), default='inlinetime')
        self.add_argument('--refresh', type=float, default=1)

    def timer(self):
        return time.perf_counter()

    def human_num(self, num, prec=3):
        sign = '-' if num < 0 else ''
        num = abs(num)
        if num > 1000000000000:
            suffix = 't'
            num /= 1000000000000
        elif num > 1000000000:
            suffix = 'b'
            num /= 1000000000
        elif num > 1000000:
            suffix = 'm'
            num /= 1000000
        elif num > 1000:
            suffix = 'k'
            num /= 1000
        else:
            suffix = ''
        if num > 100:
            prec -= 3
        elif num > 10:
            prec -= 2
        elif num > 1:
            prec -= 1
        prec = max(prec, 0)
        fmt = '%%.%df' % prec
        snum = fmt % num
        if '.' in snum:
            snum = snum.rstrip('0').rstrip('.')
        return '%s%s%s' % (sign, snum, suffix)

    def run(self, args):
        print('\0337')  # save
        print('\033[?25l')  # hide cursor
        print('\033[2J')  # clear
        try:
            self._run(args)
        finally:
            print('\033[?25h')  # restore cursor
            print('\0338')  # restore

    def _run(self, args):
        requests.put(args.url + self.urn + 'start')
        prev_totals = {}
        prev_ts = None
        while True:
            height = shutil.get_terminal_size()[1]
            report = requests.get(args.url + self.urn + 'report')
            ts = self.timer()
            if not report.ok:
                print(report.json())
                return
            totals = {}
            for stats in report.json():
                for x in stats:
                    key = (
                        x['call']['file'],
                        x['call']['function'],
                        x['call']['lineno']
                    )
                    try:
                        ref = totals[key]
                    except KeyError:
                        totals[key] = x['stats']
                    else:
                        ref['totaltime'] += x['stats']['totaltime']
                        ref['inlinetime'] += x['stats']['inlinetime']
                        ref['callcount'] += x['stats']['callcount']
            if prev_ts is None:
                prev_ts = ts
                prev_totals = totals
                shellish.vtmlprint("<b>Collecting...</b>")
                time.sleep(args.refresh)
                continue
            period = ts - prev_ts
            for call, stats in totals.items():
                if call in prev_totals:
                    prev = prev_totals[call]
                    sample_total = stats['inlinetime'] - prev['inlinetime']
                    sample_calls = stats['callcount'] - prev['callcount']
                    stats['cpu_percent'] = sample_total / period
                    stats['call_rate'] = sample_calls / period
                    if sample_calls:
                        stats['percall_time'] = sample_total / sample_calls
                    else:
                        stats['percall_time'] = 0
                else:
                    stats['cpu_percent'] = 0
                    stats['call_rate'] = 0
                    stats['percall_time'] = 0
            prev_ts = ts
            prev_totals = totals
            stats = sorted(totals.items(), key=lambda x: x[1][args.sortby],
                           reverse=True)
            del stats[height-3:]
            table = shellish.Table(headers=[
                'Function',
                'CPU%',
                'Inline-Time',
                'Total-Time',
                'Time/call',
                'Calls/s',
                'Calls',
            ])
            print('\033[H')  # Move cursor home
            table.print([
                '%s:%s:%s' % ('/'.join(x[0][0].rsplit('/', 2)[-2:]), x[0][1],
                              x[0][2]),
                self.human_num((x[1]['cpu_percent'] * 100), prec=1),
                self.human_num(x[1]['inlinetime']),
                self.human_num(x[1]['totaltime']),
                '%.0f μs' % (x[1]['percall_time'] * 1000000),
                self.human_num(x[1]['call_rate']),
                self.human_num(x[1]['callcount'])
            ] for x in stats)
            time.sleep(args.refresh)



def entry():
    AIOClusterControl()()
