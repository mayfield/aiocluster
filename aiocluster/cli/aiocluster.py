"""
Command line interface for managing a simple aiocluster service.
"""

import asyncio
import shellish
import logging.handlers
from ..import coordinator


class AIOCluster(shellish.Command):
    """ Bootstrap a simple AIOCluster service.

    Use this tool to run a multiprocess service when you do not need custom
    coordinator behavior.  A stock Coordinator will be used to kickoff worker
    processes. """

    name = 'aiocluster'
    default_log_format = ' '.join((
        '[%(asctime)s]',
        '[pid:%(process)s]',
        '[%(name)s]',
        '[%(levelname)s]',
        '%(message)s'
    ))
    verbose_log_format = ' '.join((
        '[%(asctime)s]',
        '[pid:%(process)s:%(threadName)s]',
        '[%(name)s]',
        '[%(levelname)s]',
        '[%(filename)s:%(funcName)s():%(lineno)s]',
        '%(message)s'
    ))


    def setup_args(self, parser):
        self.add_argument('worker_spec', metavar='MODULE:FUNCTION',
                          help='The module/function specification for worker '
                          'processes. The module needs to be in Python\'s '
                          'module search path.')
        self.add_argument('--uvloop', choices=('auto', 'on', 'off'),
                          help='[auto] Optional use of faster event loop from '
                          'https://github.com/MagicStack/uvloop')
        self.add_argument('--workers', help='Number of worker processes to '
                          'run.')
        self.add_argument('--log-handler', choices=('color', 'off', 'syslog'),
                          default='color', help='[color] Adjust log handler '
                          'for coordinator and workers.')
        levels = 'debug', 'info', 'warning', 'error', 'critical'
        self.add_argument('--log-level', choices=levels, default='info',
                          help='[info] Choose default logging level.')
        self.add_argument('--log-format', help='Override the logging format')
        self.add_argument('--syslog-addr', default='/dev/log',
                          help='[/dev/log] Either a unix socket or '
                          '`host:port` tuple.')
        self.add_argument('--verbose', '-v', action='store_true',
                          help='Verbose log output')

    def run(self, args):
        if args.uvloop in {'auto', 'yes'}:
            try:
                import uvloop
            except ImportError:
                uvloop = None
            if args.uvloop == 'yes' and uvloop is None:
                raise SystemExit("uvloop module not found")
            if uvloop is not None:
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        if args.log_handler != 'off':
            if args.log_format is not None:
                log_format = args.log_format
            elif args.verbose:
                log_format = self.verbose_log_format
            else:
                log_format = self.default_log_format
            if args.log_handler == 'syslog':
                addr = args.syslog_addr
                try:
                    host, port = addr.split(':', 1)
                    port = int(port)
                except ValueError:
                    pass
                else:
                    addr = host, port
                handler = logging.handlers.SysLogHandler(addr)
                handler.setFormatter(logging.Formatter(log_format))
            else:
                handler = shellish.logging.VTMLHandler(fmt=log_format)
            root = logging.getLogger()
            root.addHandler(handler)
            root.setLevel(args.log_level.upper())
        loop = asyncio.get_event_loop()
        coord = coordinator.Coordinator(args.worker_spec,
                                        worker_count=args.workers)
        loop.run_until_complete(coord.start())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete((coord.stop()))
            loop.close()


def entry():
    AIOCluster()()
