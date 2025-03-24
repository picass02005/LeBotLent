# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import asyncio
import datetime
from datetime import timezone
from typing import Dict


def transform_str_to_datetime_args(text: str) -> Dict[str, int]:
    ret = {}

    for i in text.split(" "):
        match i[-1].lower():
            case "d":
                key = "days"
            case "w":
                key = "weeks"

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


def compact_str_to_human(compact_str: str) -> str:
    ret = []

    for k, v in transform_str_to_datetime_args(compact_str).items():
        if v == 1:
            ret.append(f"{v} {k[:-1]}")

        else:
            ret.append(f"{v} {k}")

    return ' '.join(ret)


async def wait_specific_time(hours: int = 0, minutes: int = 0, seconds: int = 0) -> None:
    """
    Wait until a precize time (in UTC)
    :param hours: Hours
    :param minutes: Minutes
    :param seconds: Seconds
    :return: None
    """

    given_time = datetime.time(hours, minutes, seconds, tzinfo=timezone.utc)
    now = datetime.datetime.now(tz=timezone.utc)
    future_exec = datetime.datetime.combine(now, given_time)

    if (future_exec - now).days < 0:  # If we are past the execution, it will take place tomorrow
        future_exec = datetime.datetime.combine(now + datetime.timedelta(days=1), given_time)  # days always >= 0

    await asyncio.sleep((future_exec - now).total_seconds())
