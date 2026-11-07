import copy
from bot1.sources.fake import sample_event


def event(index=10, **kwargs):
    return sample_event(index, **kwargs)


def with_records(records, stream="test", end=None):
    return {"schema": "synthetic-history-v1", "stream": stream,
            "expected_end": len(records) if end is None else end,
            "records": [{"offset": i, "event": copy.deepcopy(e)} for i, e in enumerate(records, 1)]}
