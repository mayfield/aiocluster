"""
Route URLs to correct resource handler.
"""

from . import profiler, memory, ps
from .. import util

router = util.Router({
    'profiler': profiler.ProfilerView,
    'memory': memory.Memory(),
    'ps': ps.PSResrouce()
})
