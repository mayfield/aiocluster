"""
Command line interface for managing a simple aiocluster service.
"""

import argparse
import logging.handlers
import pkg_resources
import shellish
from .. import coordinator, setup

logger = logging.getLogger('cli.aiocluster')

worker_arg_config = {
    "dest": 'worker_spec',
    "metavar": 'MODULE:FUNCTION',
    "help": 'The module/function specification for worker processes. The '
            'module needs to be in the Python module search path.'
}


class AIOCluster(shellish.Command):
    """ Bootstrap a simple AIOCluster service.

    Use this tool to run a multiprocess service when you do not need custom
    coordinator behavior.  A stock Coordinator will be used to kickoff worker
    processes. """

    name = 'aiocluster'
    options_desc = 'The options affect the overall cluster operation.'

    def __init__(self, worker):
        self._worker = worker
        super().__init__()

    def setup_args(self, parser):
        self.add_argument(**worker_arg_config)
        self._std_arg_parser = parser.add_argument_group(
            title='coordinator options', description=self.options_desc)
        self._adv_arg_parser = parser.add_argument_group(
            title='advanced coordinator options')

        self._arg('--workers', type=int, help='Number of worker processes '
                  'to run')
        self._arg('--log-handler', choices=('console', 'off', 'syslog'),
                  default='console', help='Set the log handler for the '
                  'coordinator workers.')
        levels = 'debug', 'info', 'warning', 'error', 'critical'
        self._arg('--log-level', choices=levels, default='info',
                  help='Log level for cooordinator and workers.')
        self._arg('--verbose', '-v', action='store_true', autoenv=True,
                  help='Verbose log output.')
        version = pkg_resources.require("aiocluster")[0].version
        self._arg('--version', action='version', version=version)

        self._advarg('--event-loop', choices=('auto', 'uvloop', 'default'),
                     default='auto', autoenv=True, help='Select the event '
                     'loop policy to use.  The `auto` mode will try to use '
                     'uvloop if available.')
        self._advarg('--event-loop-debug', action='store_true', autoenv=True,
                     help='Enable event loop debug mode.')
        self._advarg('--disable-worker-restart', action='store_true',
                     autoenv=True, help='Disable automatic restart of worker '
                     'processes if they exit or fail.')
        self._advarg('--log-format', autoenv=True, help='Override the default '
                     'logging format.')
        self._advarg('--syslog-addr', default='/dev/log', autoenv=True,
                     help='Either a unix socket filename or `host:port`.')
        self._advarg('--disable-diag', action='store_true', autoenv=True,
                     help='Disable the diagnostic service.')
        self._advarg('--diag-addr', default='0.0.0.0', autoenv=True,
                     help='Local address to bind diagnostic server on.')
        self._advarg('--diag-port', default=7878, type=int, autoenv=True,
                     help='Port to bind diag server on.')
        #self.add_subcommand(self._worker)

    def _arg(self, *args, parser=None, autoenv=True, **kwargs):
        if parser is None:
            parser = self._std_arg_parser
        return self.add_argument(*args, parser=parser, autoenv=autoenv,
                                 **kwargs)

    def _advarg(self, *args, **kwargs):
        return self._arg(*args, parser=self._adv_arg_parser, **kwargs)

    def run(self, args):
        worker_settings = {}
        if args.log_handler != 'off':
            worker_settings['logging'] = {
                "kind": args.log_handler,
                "level": args.log_level,
                "fmt": args.log_format,
                "verbose": args.verbose,
                "syslog_addr": args.syslog_addr,
            }
            setup.setup_logging(**worker_settings['logging'])
        logger.info("Starting Coordinator")
        worker_settings['event_loop'] = {
            "policy": args.event_loop,
            "debug": args.event_loop_debug
        }
        if not args.disable_diag:
            diag_settings = {
                "addr": args.diag_addr,
                "port": args.diag_port,
            }
        else:
            diag_settings = {}
        loop = setup.get_event_loop(**worker_settings['event_loop'])
        worker_restart = not args.disable_worker_restart
        coord = coordinator.Coordinator(args.worker_spec,
                                        worker_count=args.workers,
                                        worker_settings=worker_settings,
                                        worker_restart=worker_restart,
                                        diag_settings=diag_settings,
                                        loop=loop)
        loop.run_until_complete(coord.start())
        try:
            loop.run_until_complete(coord.wait_stopped())
        except KeyboardInterrupt:
            pass
        loop.close()


def entry():
    """ We perform some magic here to extract the worker_spec from the args
    before invoking the more complicated argument parsing of the coordinator
    and its workerservice command. """
    sniff = argparse.ArgumentParser()
    sniff.add_argument(**worker_arg_config)
    #sniff.add_argument('x', nargs=argparse.REMAINDER)
    args = sniff.parse_known_args()[0]
    worker = setup.find_worker(args.worker_spec)
    print("found something", worker)
    AIOCluster(worker)()  # reevals entire sys.argv
