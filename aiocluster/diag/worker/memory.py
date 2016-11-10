"""
Report memory usage in detail.
"""

import io
import objgraph


class MemoryRPCHandler(object):
    """ Interface to objgraph calls for finding memory mgmt problems. """

    def __init__(self, rpc_plugin):
        rpc_plugin.add_handler('memory_report', self.report)
        rpc_plugin.add_handler('memory_growth', self.growth)

    async def report(self, limit=None):
        return objgraph.most_common_types(shortnames=False, limit=limit)

    async def growth(self, limit=None):
        buf = io.StringIO()
        objgraph.show_growth(shortnames=False, limit=limit, file=buf)
        result = []
        for line in buf.getvalue().splitlines():
            name, count, change = line.rsplit(maxsplit=2)
            count = int(count)
            change = int(change.strip('+'))
            result.append((name, count, change))
        return result
