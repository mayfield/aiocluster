"""
Handle setup for both coordinator and workers.
"""

import asyncio
import importlib
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


def get_event_loop(policy='auto', debug=None):
    """ Possibly set the event loop policy to use a designer event loop.
    Return a default event loop (using the new policy) and possibly enable
    debug. """
    if policy in {'auto', 'uvloop'}:
        try:
            import uvloop
        except ImportError:
            uvloop = None
        if uvloop is None and policy == 'uvloop':
            raise SystemExit("uvloop module not available")
        if uvloop is not None:
            logger.debug("Using uvloop")
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    if debug is not None:
        loop.set_debug(debug)
    return loop


def find_worker(spec):
    """ Return a worker coroutine/service by its spec.  A spec is simply dot
    seperated symbols.  It should begin with the module path to the remaining
    object/function path within the final module's namespace.

        MODULE.[MODULE ...].[[OBJECT].]CALLABLE

        Eg.  some.relative.module.MyType.awaitable_function
             mymodule.myfunction
    """
    parts = spec.split('.')
    if len(parts) == 1 or '' in parts:
        raise ValueError("Invalid Spec")
    final_import_exc = None
    func_parts = None
    module = None
    for i in range(len(parts), 0, -1):
        modulepath = '.'.join(parts[:i])
        func_parts = parts[i:]
        try:
            module = importlib.import_module(modulepath)
        except ImportError as e:
            final_import_exc = e
        else:
            if not func_parts:
                raise TypeError('Spec refers to a module')
            break
    else:
        if final_import_exc:
            raise final_import_exc
    if module is None:
        raise RuntimeError(spec, func_parts)
    assert func_parts
    offt = module
    for x in func_parts:
        offt = getattr(offt, x)
    return offt
