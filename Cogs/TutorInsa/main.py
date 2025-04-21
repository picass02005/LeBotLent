# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3
from typing import Tuple, List

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from Cogs.TutorInsa.Transformers.add_rm_class_role import AddClassRoleTransformer, RemoveClassRoleTransformer
from Cogs.TutorInsa.Types.ClassEntry import ClassEntry
from GlobalModules.GetConfig import get_config
from GlobalModules.HasPerm import has_perm

PTR_DB: List[sqlite3.Connection] = []

# === DO NOT CHANGE CLASS NAME OR __init__ PARAMETERS === #
class TutorInsa(commands.GroupCog):
    global PTR_DB

    def __init__(self, bot: commands.AutoShardedBot, database: sqlite3.Connection):
        self.bot: bot = bot
        self.database = database

        self.database_check()

    def database_check(self) -> None:
        self.database.execute(
            "CREATE TABLE IF NOT EXISTS TUTOR_ROLES ("
            "ROLE_ID UNSIGNED INT,"
            "GUILD_ID UNSIGNED INT,"
            "CLASS TEXT);"
        )

        self.database.commit()

    @app_commands.command(name="add_class_role", description="Add a class role association in database")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def add_class_role(
            self,
            interaction: Interaction,
            class_name: app_commands.Transform[None | Tuple[str, ClassEntry], AddClassRoleTransformer(PTR_DB)],
            role: discord.Role
    ):

        if class_name is None:
            return

        class_id: str = class_name[0]
        class_entry: ClassEntry = class_name[1]

        count = self.database.execute(
            "SELECT COUNT(*) FROM TUTOR_ROLES WHERE CLASS=? AND GUILD_ID=?;",
            (class_id, interaction.guild_id)
        ).fetchone()[0]

        if count != 0:
            await interaction.response.send_message(
                f"Class `{class_entry.name}` is already in database",
                ephemeral=True
            )
            return

        count = self.database.execute(
            "SELECT COUNT(*) FROM TUTOR_ROLES WHERE ROLE_ID=? AND GUILD_ID=?;",
            (role.id, interaction.guild_id)
        ).fetchone()[0]

        if count != 0:
            await interaction.response.send_message(
                f"Role `{role.name}` (id: `{role.id}`) is already in database",
                ephemeral=True
            )
            return

        self.database.execute(
            "INSERT INTO TUTOR_ROLES (ROLE_ID,GUILD_ID,CLASS) VALUES (?,?,?);",
            (role.id, interaction.guild_id, class_id)
        )
        self.database.commit()

        await interaction.response.send_message(
            f"Successfully associated class `{class_entry.name}` with role `{role.name}` in database",
            ephemeral=True
        )

    @app_commands.command(name="remove_class_role", description="Remove a class role association in database")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def remove_class_role(
            self,
            interaction: Interaction,
            class_name: app_commands.Transform[None | Tuple[str, ClassEntry], RemoveClassRoleTransformer(PTR_DB)]
    ):

        if class_name is None:
            return

        class_id: str = class_name[0]
        class_entry: ClassEntry = class_name[1]

        count = self.database.execute(
            "SELECT COUNT(*) FROM TUTOR_ROLES WHERE CLASS=? AND GUILD_ID=?;",
            (class_id, interaction.guild_id)
        ).fetchone()[0]

        if count == 0:
            await interaction.response.send_message(
                f"Class `{class_entry.name}` is not in database.",
                ephemeral=True
            )
            return

        self.database.execute(
            "DELETE FROM TUTOR_ROLES WHERE CLASS=? AND GUILD_ID=?;",
            (class_id, interaction.guild_id)
        )
        self.database.commit()

        await interaction.response.send_message(
            f"Class `{class_entry.name}` successfully removed from database for this guild.",
            ephemeral=True
        )

    # TODO: List


# === DO NOT REMOVE THE FOLLOWING OR CHANGE PARAMETERS === #

async def setup(bot: commands.AutoShardedBot, database: sqlite3.Connection):
    global PTR_DB

    PTR_DB.append(database)

    guilds = [discord.Object(id=i, type=discord.Guild) for i in get_config("TutorInsa.guilds")]
    await bot.add_cog(TutorInsa(bot, database), guilds=guilds)

# TODO: Voir document DM discord Tabatha (06/04) pour specification complètes

# TODO: Choix role par année / PO / spécialité => Register role for each in db

# TODO: Demande de tutorat (button + view)
# TODO: Quand un tutorat est demandé, message aux tuteurs avec possibilité de l'accepter (bouton) => Assigne dans une DB

# TODO: Moyen pour les tuteurs de marquer un tutorat qui leur a été assigné comme fait + donner le temps consacré + commentaires + autre séance?
# TODO: Demande d'avis anonyme automatisée après les tutorat (view)

# TODO: Commande pour avoir un histoirque des tutorats demandés par une personne (+ le nombre)
# TODO: La même chose pour les tuteurs pour voir quels tutorats ils ont fait / le temps

# TODO: limit all actions to only tutorinsa discord => Already done for commands
# TODO: check config

# TODO: documentation pour passassion (p-e une commande pour la récupérer dispo aux respos + version pour les tuteurs)

# TODO: perms + brief
