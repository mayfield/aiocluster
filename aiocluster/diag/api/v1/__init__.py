"""
Route URLs to correct resource handler.
"""

from . import profiler, memory, ps, about
from .. import util

router = util.Router({
    'profiler': profiler.ProfilerRouter,
    'memory': memory.MemoryResource(),
    'ps': ps.PSResource(),
    'about': about.AboutResource()
}, desc="Version 1 API endpoints.")
