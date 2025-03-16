import datetime
from typing import Dict


def transform_str_to_datetime_args(text: str) -> Dict[str, int]:
    ret = {}

    for i in text.split(" "):
        match i[-1].lower():
            case "d":
                key = "days"
            case "w":
                key = "weeks"
            case "m":
                key = "months"
            case _:
                key = None

        if key is None:
            continue

        if key in ret.keys():
            ret.update({key: int(i[:-1]) + ret[key]})

        else:
            ret.update({key: int(i[:-1])})

    return ret


def date_to_timestamp(date: datetime.date) -> int:
    return int(datetime.datetime.combine(date, datetime.time(tzinfo=datetime.timezone.utc)).timestamp())
