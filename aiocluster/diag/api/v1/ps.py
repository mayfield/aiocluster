"""
/api/v1/ps handler (process stats).
"""

from .. import util
from .... import coordinator


class PSResource(util.Resource):

    async def get(self):
        coord = coordinator.get_coordinator()
        return [{
            "worker": x.ident,
        } for x in coord.workers]
