"""
Handle setup for both coordinator and workers.
"""

import asyncio
import logging.handlers
import shellish

logger = logging.getLogger('setup')

# (field, applicability)  None = any log handler
default_fmt = (
    ('[%(asctime)s]', 'console'),
    ('[pid:%(process)s]', 'console'),
    ('[%(name)s]', None),
    ('[%(levelname)s]', None),
    ('%(message)s', None)
)
verbose_fmt = (
    ('[%(asctime)s]', 'console'),
    ('[pid:%(process)s:%(threadName)s]', 'console'),
    ('[%(threadName)s]', 'syslog'),
    ('[%(name)s]', None),
    ('[%(levelname)s]', None),
    ('[%(filename)s:%(funcName)s():%(lineno)s]', None),
    ('%(message)s', None)
)


def setup_logging(kind='console', level=None, verbose=False, fmt=None,
                  syslog_addr=None):
    """ Setup the root log handler;  Similar to logging.basicConfig. """
    if kind is None:
        kind = 'console'
    if level is None:
        level = 'info'
    if fmt is None:
        fmt_tuples = default_fmt if not verbose else verbose_fmt
        fmt = ' '.join(field for field, applicability in fmt_tuples
                       if applicability in (None, kind))
    if kind == 'syslog':
        if syslog_addr is None:
            syslog_addr = '/dev/log'
        else:
            try:
                host, port = syslog_addr.split(':', 1)
                port = int(port)
            except ValueError:
                pass
            else:
                syslog_addr = host, port
        handler = logging.handlers.SysLogHandler(syslog_addr)
        handler.setFormatter(logging.Formatter(fmt))
    elif kind == 'console':
        handler = shellish.logging.VTMLHandler(fmt=fmt)
    else:
        raise TypeError("Unknown log kind: %s" % kind)
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.addHandler(handler)


def get_event_loop(use_uvloop=None, debug=None):
    """ Possibly set the event loop policy to use uvloop and always return the
    event loop that should be used by all further asyncio activity. """
    if use_uvloop in {None, True}:
        try:
            import uvloop
        except ImportError:
            uvloop = None
        if use_uvloop and uvloop is None:
            raise SystemExit("uvloop module not found")
        if uvloop is not None:
            logger.debug("Using uvloop")
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        loop = asyncio.get_event_loop()
        if debug is not None:
            loop.set_debug(debug)
    return asyncio.get_event_loop()

