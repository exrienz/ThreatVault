from collections.abc import Sequence

from sqlalchemy import Row


def list_of_rows_to_dict(data: Sequence[Row]) -> list[dict]:
    res = []
    for d in data:
        res.append(d._asdict())
    return res
