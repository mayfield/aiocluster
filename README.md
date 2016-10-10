aiocluster
========
Tools and frameworks classes for building your own asyncio cluster.  A cluster
in this case is a network of nodes (unique computers/containers) and workers
within those nodes (processes).

Each node can be made aware of other nodes using a discovery mechanism not
covered by this service.  For example a static list of IP/port tuples can be
provided to each node so they are capable of communicating with each other.
More advanced discovery techniques are encouraged for more scalable
applications, such as multicast/broadcast, DNS, consul, or AWS API depending
on your environment and needs.


Features
--------
* Full asyncio usage.  No synchronous calls are used.
* Bundled with command line facilities to help ease startup.
* Diagnostic web server interface
* Diagnostic CLI tool
* Basic multi process support (pre-fork)
* Integrated aionanomsg support for cluster management and comms
* Bring your favorite asyncio patterns and libraries!!!


Installation
--------
    python3 ./setup.py build
    python3 ./setup.py install


Compatibility
--------
* Python 3.5+
