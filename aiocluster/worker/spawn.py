"""
Process creation and management for worker processes.
"""

import asyncio
import datetime
import itertools
import logging
import os
import re
import psutil
import subprocess
import sys
from . import env

logger = logging.getLogger('worker.spawn')
default_bootloader = 'aiocluster.worker.bootloader'


async def spawn(worker_spec, **kwargs):
    """ Spawn a new python based worker process that looks very close to the
    current one.  For safety and compatibility reasons we do not use a
    fork-without-exec pattern;  Instead the current python env is inspected
    and used as a reference for a new python execution.  Arguments and context
    are serialized and passed to a bootloader function that turns them back
    into python types. """
    pycmd = sys.executable
    pyflags = subprocess._args_from_interpreter_flags()
    wp = WorkerProcess(worker_spec, pycmd, pyflags, **kwargs)
    logger.debug("Spawning new worker: %s" % wp)
    await wp.start()
    logger.info("Spawned: %s" % wp)
    return wp


class WorkerProcess(object):

    identer = itertools.count()
    spec_regex = re.compile(r'([a-z_][0-9a-z_]*(\.(?=[a-z_]))?)+', re.I)

    def __init__(self, spec, pycmd, pyflags, bootloader=default_bootloader,
                 loop=None, settings=None, context=None, args=None,
                 kwargs=None):
        self.process = None
        self.util = None
        self.ident = next(self.identer)
        self.created = self._now()
        self.spec = spec
        self._loop = loop
        self._env = os.environ.copy()
        self._env["_AIOCLUSTER_BOOTLOADER"] = env.encode({
            "args": args or (),
            "kwargs": kwargs or {},
            "context": context or {},
            "settings": settings or {}
        })
        self._cmd = pycmd, *pyflags, '-m', bootloader, spec, str(self.ident)

    def __str__(self):
        return '<%s:%d [%s] pid=%s, age=%s>' % (type(self).__name__,
            self.ident, self.spec, self.process and self.process.pid,
            self.age())

    def _now(self):
        return datetime.datetime.now()

    def age(self):
        return self._now() - self.created

    async def start(self):
        self.process = await asyncio.create_subprocess_exec(*self._cmd,
            env=self._env, loop=self._loop)
        self.util = psutil.Process(self.process.pid)
        self.util.cpu_percent(None)  # prime cpu usage stat
