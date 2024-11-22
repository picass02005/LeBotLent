import sqlite3
import time

from GlobalModules.GetConfig import get_config


def user_on_cooldown(user_id: int, database: sqlite3.Connection) -> bool:
    database.execute(
        "DELETE FROM LAST_USED_COMMANDS WHERE TIMESTAMP < ?",
        (time.time() - get_config('core.last_used_commands_timeout'),)
    )
    database.commit()

    max_per_user = get_config("core.max_used_commands_max_per_user")

    cursor = database.execute("SELECT TIMESTAMP, USER_ID FROM LAST_USED_COMMANDS WHERE USER_ID=?", (user_id,))
    fetched = cursor.fetchall()
    cursor.close()

    if len(fetched) > max_per_user:
        return True

    cursor = database.execute("SELECT TIMESTAMP, USER_ID FROM LAST_USED_COMMANDS")
    fetched = cursor.fetchall()
    cursor.close()

    if len(fetched) > get_config('core.last_used_commands_max'):
        return True

    return False
