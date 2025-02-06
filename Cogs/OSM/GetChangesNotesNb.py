from datetime import datetime, timedelta

from Cogs.OSM.Py_OSM_API import PyOSM, OSMTimeDelta, OSMSort, OSMOrder, OSMStatus


async def get_changes_nb(py_osm: PyOSM, uid: int, from_date: datetime = None) -> int:
    if from_date is None:
        from_date = datetime.fromtimestamp(0)

    changes_nb = 0

    kwargs = {
        "limit": py_osm.capabilities.changesets.maximum_query_limit,
        "user_id": uid,
        "created_timedelta": OSMTimeDelta(before=from_date),
        "status": OSMStatus.OPEN_AND_CLOSED,
        "order": OSMOrder.OLDEST
    }

    on = True
    while on:
        changesets = await py_osm.fetch_changesets_by_search(**kwargs)

        for i in changesets:
            changes_nb += i.changes_count

        if len(changesets) < kwargs["limit"]:
            on = False

        else:
            kwargs.update(
                {"created_timedelta": OSMTimeDelta(before=changesets[-1].created_at + timedelta(seconds=1))}
            )

    return changes_nb


async def get_notes_nb(py_osm: PyOSM, uid: int, from_date: datetime = None) -> int:
    if from_date is None:
        from_date = datetime.fromtimestamp(0)

    notes_nb = 0

    kwargs = {
        "limit": py_osm.capabilities.notes.maximum_query_limit,
        "closed": -1,
        "user_id": uid,
        "during": OSMTimeDelta(after=from_date),
        "sort": OSMSort.CREATED_AT,
        "order": OSMOrder.OLDEST
    }

    on = True
    while on:
        notes = await py_osm.fetch_notes_by_search(**kwargs)
        notes_nb += len(notes)

        if len(notes) < kwargs["limit"]:
            on = False

        else:
            kwargs.update({"during": OSMTimeDelta(after=notes[-1].date_created + timedelta(seconds=1))})

    return notes_nb
