# Helper to serialize datetime
from datetime import datetime


def _dt(o):
    if isinstance(o, datetime):
        return o.isoformat()
    return str(o)
