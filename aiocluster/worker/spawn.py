"""
Process creation and management for worker processes.
"""

import asyncio
import datetime
import itertools
import logging
import os
import psutil
import re
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
    """ Used by the coordinator process to track a WorkerCommand subprocess. """

    identer = itertools.count()
    spec_regex = re.compile(r'([a-z_][0-9a-z_]*(\.(?=[a-z_]))?)+', re.I)

    def __init__(self, spec, pycmd, pyflags, worker_settings=None,
                 worker_config=None, worker_args=None, loop=None,
                 bootloader=default_bootloader):
        self.util = None
        self.ident = next(self.identer)
        self.created = self._now()
        self.spec = spec
        self.process = None
        self._loop = loop
        self._env = os.environ.copy()
        self._env["_AIOCLUSTER_BOOTLOADER"] = env.encode({
            "settings": worker_settings,
            "config": worker_config,
            "args": worker_args,
        })
        self._cmd = pycmd, *pyflags, '-m', bootloader, spec, str(self.ident)

    def __str__(self):
        pid = '-' if self.process is None else self.process.pid
        return '<%s:%d [%s] pid=%s, age=%s>' % (type(self).__name__,
            self.ident, self.spec, pid, self.age())

    def _now(self):
        return datetime.datetime.now()

    def age(self):
        return self._now() - self.created

    async def start(self):
        self.process = await asyncio.create_subprocess_exec(*self._cmd,
            env=self._env, loop=self._loop)
        self.util = psutil.Process(self.process.pid)
        self.util.cpu_percent(None)  # prime cpu usage stat
