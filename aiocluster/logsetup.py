"""
Common log setup for both coordinator and workers.
"""

import logging.handlers
import shellish

default_fmt = ' '.join((
    '[%(asctime)s]',
    '[pid:%(process)s]',
    '[%(name)s]',
    '[%(levelname)s]',
    '%(message)s'
))
verbose_fmt = ' '.join((
    '[%(asctime)s]',
    '[pid:%(process)s:%(threadName)s]',
    '[%(name)s]',
    '[%(levelname)s]',
    '[%(filename)s:%(funcName)s():%(lineno)s]',
    '%(message)s'
))


def setup_logging(kind='color', level=None, verbose=False, fmt=None,
                  syslog_addr=None):
    """ Setup the root log handler;  Similar to logging.basicConfig. """
    if kind is None:
        kind = 'color'
    if level is None:
        level = 'info'
    if fmt is None:
        fmt = default_fmt if not verbose else verbose_fmt
    if syslog_addr is None:
        syslog_addr = '/dev/log'
    if kind == 'syslog':
        handler = logging.handlers.SysLogHandler(syslog_addr)
        handler.setFormatter(logging.Formatter(fmt))
    elif kind == 'color':
        handler = shellish.logging.VTMLHandler(fmt=fmt)
    else:
        raise TypeError("Unknown log kind: %s" % kind)
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.addHandler(handler)
