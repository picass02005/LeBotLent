# SPDX-License-Identifier: MIT
# Copyright (C) 2024 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3
import time
from datetime import datetime


class Logger:
    def __init__(self, database: sqlite3.Connection):
        self.database = database

    def add_log(self, category: str, log_entry: str):
        timestamp = int(time.time())
        self.database.execute(
            "INSERT INTO LOGS (TIMESTAMP, CATEGORY, LOG) VALUES (?, ?, ?)",
            (timestamp, category, log_entry)
        )
        self.database.commit()

        print(f"[{datetime.fromtimestamp(timestamp).strftime('%H : %M : %S')} | {category}] {log_entry}")
