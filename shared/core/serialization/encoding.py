import datetime
import json
from typing import Any, Dict
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


class DatetimeEncoder(SetEncoder):
    def default(self, o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return super().default(o)


def json_encodable_dict(dict_to_encode: Dict[Any, Any]) -> Dict[Any, Any]:
    return json.loads(json.dumps(dict_to_encode, cls=DatetimeEncoder))
