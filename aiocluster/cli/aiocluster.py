"""
Command line interface for managing a simple aiocluster service.
"""

import logging.handlers
import pkg_resources
import shellish
from .. import coordinator, setup

logger = logging.getLogger('cli.aiocluster')


class AIOCluster(shellish.Command):
    """ Bootstrap a simple AIOCluster service.

    Use this tool to run a multiprocess service when you do not need custom
    coordinator behavior.  A stock Coordinator will be used to kickoff worker
    processes. """

    name = 'aiocluster'

    def setup_args(self, parser):
        self.add_argument('worker_spec', metavar='MODULE:FUNCTION',
                          autoenv=True, help='The module/function '
                          'specification for worker processes. The module '
                          'needs to be in Python\'s module search path.')
        self.add_argument('--uvloop', choices=('auto', 'on', 'off'),
                          default='auto', autoenv=True, help='Use of high '
                          'performance event loop uvloop.')
        self.add_argument('--event-loop-debug', action='store_true',
                          autoenv=True, help='Calls loop.set_debug(True)')
        self.add_argument('--workers', autoenv=True, type=int,
                          help='Number of worker processes to run.')
        self.add_argument('--log-handler', choices=('console', 'off',
                          'syslog'), default='console', autoenv=True,
                          help='Set the log handler for the coordinator '
                          'workers.')
        levels = 'debug', 'info', 'warning', 'error', 'critical'
        self.add_argument('--log-level', choices=levels, default='info',
                          autoenv=True, help='Choose default logging level.')
        self.add_argument('--log-format', autoenv=True, help='Override the '
                          'default logging format')
        self.add_argument('--syslog-addr', default='/dev/log', autoenv=True,
                          help='Either a unix socket or `host:port` tuple.')
        self.add_argument('--verbose', '-v', action='store_true', autoenv=True,
                          help='Verbose log output')
        version = pkg_resources.require("aiocluster")[0].version
        self.add_argument('--version', action='version', version=version)

    def run(self, args):
        worker_settings = {}
        if args.log_handler != 'off':
            worker_settings['logging'] = {
                "kind": args.log_handler,
                "level": args.log_level,
                "fmt": args.log_format,
                "verbose": args.verbose,
                "syslog_addr": args.syslog_addr
            }
            setup.setup_logging(**worker_settings['logging'])
        logger.info("Starting Coordinator")
        worker_settings['event_loop'] = {
            "use_uvloop": {"auto": None, "on": True, "off": False}[args.uvloop]
        }
        loop = setup.get_event_loop(**worker_settings['event_loop'])
        coord = coordinator.Coordinator(args.worker_spec,
                                        worker_count=args.workers,
                                        worker_settings=worker_settings,
                                        loop=loop)
        loop.run_until_complete(coord.start())
        try:
            loop.run_until_complete(coord.wait_stopped())
        except KeyboardInterrupt:
            pass
        finally:
            try:
                loop.run_until_complete(coord.stop())
            finally:
                loop.close()


def entry():
    AIOCluster()()
