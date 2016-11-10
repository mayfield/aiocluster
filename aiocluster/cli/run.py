"""
Command line interface for managing a simple aiocluster service.
"""

import argparse
import pkg_resources
import shellish
import shlex
from .. import coordinator, setup


class RunCommand(shellish.Command):
    """ Run a cluster of aio worker commands. """

    name = 'run'
    options_desc = 'These options affect the overall cluster operation.'

    def setup_args(self, parser):
        self._std_arg_parser = parser.add_argument_group(
            title='coordinator options', description=self.options_desc)
        self._adv_arg_parser = parser.add_argument_group(
            title='advanced coordinator options')

        # Coord args...
        self._arg('--workers', metavar='NUM_PROCS', type=int,
                  help='Number of worker processes to run')
        self._arg('--log-handler', choices=('console', 'off', 'syslog'),
                  default='console', help='Set the log handler for the '
                  'coordinator workers.')
        levels = 'debug', 'info', 'warning', 'error', 'critical'
        self._arg('--log-level', choices=levels, default='info',
                  help='Log level for coordinator and workers.')
        self._arg('--verbose', action='store_true', help='Verbose log output.')
        version = pkg_resources.require("aiocluster")[0].version
        self._arg('--version', action='version', version=version)

        # Advanced args...
        self._advarg('--event-loop', choices=('auto', 'uvloop', 'default'),
                     default='auto', help='Select the event loop policy.  '
                     'The `auto` mode will try to use uvloop if available.')
        self._advarg('--event-loop-debug', action='store_true',
                     help='Enable event loop debug mode.')
        self._advarg('--disable-worker-restart', action='store_true',
                     help='Disable automatic restart of worker processes if '
                     'they exit or fail.')
        self._advarg('--log-format', metavar='TEMPLATE', help='Override the '
                     'logging format.')
        self._advarg('--syslog-addr', default='/dev/log', help='Either a '
                     'unix socket filename or `host:port`.')
        self._advarg('--disable-diag', action='store_true', help='Disable '
                     'the diagnostic service.')
        self._advarg('--diag-addr', metavar='BIND_IP', default='0.0.0.0',
                     help='Local address to bind diagnostic server on.')
        self._advarg('--diag-port', metavar='BIND_PORT', default=7878,
                     type=int, help='Port to bind diag server on.')

        wspec_doc = 'The worker specification is a dot notation string ' \
            '<cyan>(ie. foo.bar)</cyan> that refers to the module(s) and ' \
            'call within that module to be used as the worker process in ' \
            'an aiocluster.  The worker call can be a regular function, a ' \
            'coroutine function, or a subclass of `WorkerCommand`.\n\n' \
            '<b>Note, the module must be in the Python module search path.' \
            '</b>\n\n' \
            'Examples...\n\n' \
            '    <blue>datetime.datetime.now</blue>\n\n' \
            '    <blue>foo.module.UnrelatedType.some_class_func</blue>\n\n' \
            '    <blue>my_project.MyWorkerCommand</blue>\n'
        wspec = parser.add_argument_group(title='worker specification',
                                          description=wspec_doc)
        self.add_argument('worker_spec', parser=wspec, help='Dot notation ' \
                          'accessor string for a worker callable/type.')
        self.add_argument('worker_args', parser=wspec,
                          nargs=argparse.REMAINDER, help='Any arguments '
                          'designated for the worker command.')

    def _arg(self, *args, parser=None, autoenv=True, **kwargs):
        if parser is None:
            parser = self._std_arg_parser
        return self.add_argument(*args, parser=parser, autoenv=autoenv,
                                 **kwargs)

    def _advarg(self, *args, **kwargs):
        return self._arg(*args, parser=self._adv_arg_parser, **kwargs)

    def run(self, args):
        """ Validate the args work with our worker by instantiating it here.
        if it checks out and doesn't exit via a `--help` or other type of
        SystemExit then we start the coordinator and save the arguments used
        just for the worker to be proxied to the worker processes. """
        try:
            worker = setup.find_worker(args.worker_spec)
        except (ValueError, AttributeError, ImportError, TypeError) as e:
            shellish.vtmlprint("<b><red>Find Worker Error:</red> %s" % e)
            raise SystemExit(1)
        worker_cmd = setup.worker_coerce(worker)()
        worker_argv = ' '.join(map(shlex.quote, args.worker_args))
        worker_args = vars(worker_cmd.parse_args(worker_argv))
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
                                        worker_args=worker_args,
                                        worker_restart=worker_restart,
                                        diag_settings=diag_settings,
                                        loop=loop)
        loop.run_until_complete(coord.start())
        try:
            loop.run_until_complete(coord.wait_stopped())
        except KeyboardInterrupt:
            pass
        loop.close()
