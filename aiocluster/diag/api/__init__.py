"""
Route API calls to correct sub handlers.
"""

from . import util, v1

router = util.Router({
    'v1': v1.router
})
