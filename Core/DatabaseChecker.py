import sqlite3


def check_database(database: sqlite3.Connection) -> None:
    """
    Check the database and add necessary fields
    :param database: The database to check
    :return: None
    """

    database.execute(
        "CREATE TABLE IF NOT EXISTS LOGS ("
        "ID INTEGER PRIMARY KEY,"
        "TIMESTAMP UNSIGNED INT(10),"
        "CATEGORY TEXT,"
        "LOG TEXT);"
    )

    database.execute(
        "CREATE TABLE IF NOT EXISTS LAST_USED_COMMANDS ("
        "TIMESTAMP UNSIGNED INT(10),"
        "USER_ID INT);"
    )

    database.execute(
        "CREATE TABLE IF NOT EXISTS PAGINATOR ("
        "MESSAGE_ID INTEGER INT,"
        "CHANNEL_ID INTEGER INT,"
        "GUILD_ID INTEGER INT,"
        "USER_ID INTEGER INT,"
        "DELETE_TS UNSIGNED INT(10),"
        "PAGES JSON,"
        "CURRENT_PAGE INT);"
    )

    database.execute(
        "CREATE TABLE IF NOT EXISTS ERROR_REPORT ("
        "ID INTEGER PRIMARY KEY,"
        "USER_ID INTEGER INT,"
        "USER_NAME TEXT,"
        "COMMAND TEXT,"
        "BRIEF_ERROR TEXT,"
        "FULL_ERROR TEXT,"
        "ARGS_KWARGS JSON,"
        "EXTRA_DATA JSON,"
        "DELETE_TS UNSIGNED INT(10));"
    )

    database.commit()
