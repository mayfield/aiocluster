"""
Command line interface for managing a simple aiocluster service.
"""

import asyncio
import logging.handlers
import pkg_resources
import shellish
from ..import coordinator

logger = logging.getLogger('aiocluster.cli')


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
                          autoenv=True, help='The module/function '
                          'specification for worker processes. The module '
                          'needs to be in Python\'s module search path.')
        self.add_argument('--uvloop', choices=('auto', 'on', 'off'),
                          default='auto', autoenv=True, help='Use of high '
                          'performance event loop uvloop.')
        self.add_argument('--workers', autoenv=True, type=int,
                          help='Number of worker processes to run.')
        self.add_argument('--log-handler', choices=('color', 'off', 'syslog'),
                          default='color', autoenv=True, help='Set the log '
                          'handler for the coordinator and its workers.')
        levels = 'debug', 'info', 'warning', 'error', 'critical'
        self.add_argument('--log-level', choices=levels, default='info',
                          autoenv=True, help='Choose default logging level.')
        self.add_argument('--log-format', autoenv=True, help='Override the '
                          'logging format')
        self.add_argument('--syslog-addr', default='/dev/log', autoenv=True,
                          help='Either a unix socket or `host:port` tuple.')
        self.add_argument('--verbose', '-v', action='store_true', autoenv=True,
                          help='Verbose log output')
        version = pkg_resources.require("aiocluster")[0].version
        self.add_argument('--version', action='version', version=version)

    def run(self, args):
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
        logger.info("Starting Coordinator")
        if args.uvloop in {'auto', 'yes'}:
            try:
                import uvloop
            except ImportError:
                uvloop = None
            if args.uvloop == 'yes' and uvloop is None:
                raise SystemExit("uvloop module not found")
            if uvloop is not None:
                logger.info("Using high performance uvloop.")
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        loop = asyncio.get_event_loop()
        coord = coordinator.Coordinator(args.worker_spec,
                                        worker_count=args.workers)
        loop.run_until_complete(coord.start())
        try:
            loop.run_until_complete(coord.wait_stopped())
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(coord.stop())
            loop.close()


def entry():
    AIOCluster()()
