"""
Report memory usage in detail.
"""

import objgraph


class MemoryRPCHandler(object):
    """ Interface to objgraph calls for finding memory mgmt problems. """

    def __init__(self, worker):
        worker.add_worker_rpc_callback(self.report, 'memory_report')

    async def report(self):
        return objgraph.most_common_types()
