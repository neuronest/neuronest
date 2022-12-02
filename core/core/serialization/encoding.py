import json
from uuid import UUID

import numpy as np


class UUIDEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, UUID):
            return str(o)
        return super().default(o)


class NumpyEncoder(UUIDEncoder):
    def default(self, o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, np.bool_):
            return bool(o)
        return super().default(o)


class SetEncoder(NumpyEncoder):
    def default(self, o):
        if isinstance(o, set):
            return list(o)
        return super().default(o)
