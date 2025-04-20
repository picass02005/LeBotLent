# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import json
import sqlite3
from typing import Dict, List, Any, Tuple

from discord import app_commands, Interaction
from discord.app_commands import Choice

from Cogs.TutorInsa.Types.ClassEntry import ClassEntry


class BaseTransformer(app_commands.Transformer):
    def __init__(self):
        self.cache: Dict[str, ClassEntry] = {}

        self.update_cache()

    def update_cache(self) -> None:
        self.cache = {}
        with open("Cogs/TutorInsa/Config/classes.json", "r") as f:
            for k, v in json.loads(f.read()).items():
                self.cache.update({k: ClassEntry(v)})

    def check_validity(self, key: str) -> bool:
        return key in self.cache.keys()

    def prioritize_choices(self, value: str):
        priority = [(k, k.count(value)) for k in self.cache.keys() if self.check_validity(k)]
        priority.sort(key=lambda x: x[1], reverse=True)

        if priority[0][1] > 0:
            priority = [i for i in priority if i[1] > 0]

        else:
            priority.sort(key=lambda x: x[0])

        return [i[0] for i in priority[:25]]

    def autocomplete_before(self, interaction: Interaction, value: str) -> None:
        pass

    def transform_before(self, interaction: Interaction, value: str) -> None:
        pass

    async def autocomplete(self, interaction: Interaction, value: str) -> List[Choice[str]]:
        self.autocomplete_before(interaction, value)
        return [app_commands.Choice(name=i, value=i) for i in self.prioritize_choices(value)]

    async def transform(self, interaction: Interaction, value: Any, /) -> Tuple[str, ClassEntry] | None:
        self.update_cache()
        self.transform_before(interaction, value)

        if self.check_validity(value):
            return value, self.cache.get(value)

        else:
            await interaction.response.send_message(
                "Unknown value given as class identifier.\n"
                "# Valid keys are pre-filled.",
                ephemeral=True
            )
            return None


class AddClassRoleTransformer(BaseTransformer):
    def __init__(self, db: List[sqlite3.Connection]):
        super().__init__()

        self.db_list = db

        self.valid: List[str] = []
        self.guild_id: int = 0

    def update_valid(self):
        db = self.db_list[0]
        inside = [i[0] for i in db.execute(
            "SELECT CLASS FROM TUTOR_ROLES WHERE GUILD_ID=?;",
            (self.guild_id,)
        ).fetchall()]

        self.valid = [i for i in self.cache.keys() if i not in inside]

    def autocomplete_before(self, interaction: Interaction, value: str) -> None:
        if self.guild_id != interaction.guild_id or not value:
            self.guild_id = interaction.guild_id
            self.update_valid()

    def transform_before(self, interaction: Interaction, value: str) -> None:
        self.update_valid()

    def check_validity(self, key: str) -> bool:
        return key in self.valid
