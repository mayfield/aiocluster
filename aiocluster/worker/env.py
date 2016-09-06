"""
Serializer using environment vars.
"""

import base64
import pickle


def encode(data):
    return base64.b64encode(pickle.dumps(data))


def decode(value):
    return pickle.loads(base64.b64decode(value))

