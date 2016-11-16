"""
Route URLs to correct resource handler.
"""

from . import profiler, memory, ps, about
from .. import util

router = util.Router({
    'profiler': profiler.ProfilerView,
    'memory': memory.MemoryResource(),
    'ps': ps.PSResource(),
    'about': about.AboutResource()
})
