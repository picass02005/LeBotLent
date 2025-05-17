# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import json
import sqlite3
from typing import Tuple, List, Dict

import discord
from discord import app_commands, Interaction, InteractionType
from discord.ext import commands

from Cogs.TutorInsa.RoleSelectorManager import RoleSelectorManager, SelectorCallbacks
from Cogs.TutorInsa.Transformers.AddRmClassRole import AddClassRoleTransformer, RemoveClassRoleTransformer
from Cogs.TutorInsa.TutorRequestUtils import send_tutor_request_message, delete_tutor_request_message, \
    tutor_request_callback, TutorAcceptCallback
from Cogs.TutorInsa.Types.ClassEntry import ClassEntry
from GlobalModules.GetConfig import get_config
from GlobalModules.HasPerm import has_perm
from GlobalModules.Paginator import Paginator

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

        self.database.execute(
            "CREATE TABLE IF NOT EXISTS TUTOR_ROLES_SELECTOR ("
            "MESSAGE_ID UNSIGNED INT,"
            "CHANNEL_ID UNSIGNED INT,"
            "GUILD_ID UNSIGNED INT);"
        )

        self.database.execute(
            "CREATE TABLE IF NOT EXISTS TUTOR_REQUEST ("
            "REQ_MSG_ID UNSIGNED INT,"
            "REQ_CHANNEL_ID UNSIGNED INT,"
            "TUTOR_REQ_CHANNEL_ID UNSIGNED INT,"
            "TUTOR_ACCEPT_CHANNEL_ID UNSIGNED INT,"
            "GUILD_ID UNSIGNED INT);"
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

    @app_commands.command(name="list_class_role", description="List all class role association in database")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def list_class_role(self, interaction: Interaction):
        with open("Cogs/TutorInsa/Config/classes.json", "r") as f:
            classes_json = json.loads(f.read())

        by_years: Dict[int, List[Tuple[ClassEntry, int]]] = dict()
        unassigned: List[str] = list(classes_json.keys())

        for i in self.database.execute(
                "SELECT CLASS, ROLE_ID FROM TUTOR_ROLES WHERE GUILD_ID=?;",
                (interaction.guild_id,)
        ).fetchall():
            if i[0] in classes_json.keys():
                entry = ClassEntry(classes_json[i[0]])
                unassigned.remove(i[0])

                if entry.year in by_years.keys():
                    by_years[entry.year].append((entry, i[1]))

                else:
                    by_years.update({entry.year: [(entry, i[1])]})

            else:
                await interaction.response.send_message(
                    "There was an error while reading database, please contact picasso2005 / `clementduran0@gmail.com`",
                    ephemeral=True
                )
                return

        paginator = Paginator(self.database)
        guild_no_cache = await self.bot.fetch_guild(interaction.guild_id)

        for k, v in by_years.items():
            e = discord.Embed(
                title=f"Year {k}",
                description=f"List of classes / roles associations currently registered for year {k}"
            )

            for i in v:
                entry = i[0]
                role_id = i[1]
                role = guild_no_cache.get_role(role_id)
                e.add_field(
                    name=entry.name,
                    value=f"Role: `{role_id} | {role.name if role is not None else "NAME ERROR"}`\n"
                          f"Department: {entry.department}\n"
                          f"PO: {entry.po}\n"
                          f"Speciality: {entry.speciality}",
                    inline=True
                )

            paginator.add_page(e, page_name=f"Year {k}")

        if unassigned:
            max_unassigned = len(unassigned) // 10
            for j in range(max_unassigned + 1):
                page_nb = f"({j + 1}/{max_unassigned + 1})" if max_unassigned > 0 else ""
                e = discord.Embed(
                    title=f"Unassigned classes {page_nb}",
                    description="List of classes which are associated with no roles",
                    color=0xFF0000
                )

                for i in unassigned[10 * j:10 * (j + 1)]:
                    entry = ClassEntry(classes_json[i])
                    e.add_field(
                        name=entry.name,
                        value=f"Department: {entry.department}\n"
                              f"PO: {entry.po}\n"
                              f"Speciality: {entry.speciality}",
                        inline=True
                    )

                paginator.add_page(e, page_name=f"Unassigned {page_nb}")

        if unassigned:
            kwargs = {"content": f"# WARNING\n"
                                 f"You have {len(unassigned)} classes not assigned.\n"
                                 f"A list of them is present in the lasts pages."}

        else:
            kwargs = dict()

        await paginator.send_paginator(
            interaction,
            ephemeral=True,
            **kwargs
        )

    @app_commands.command(name="role_selector_manager", description="Manage the role selector message of this guild")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def role_selector_manager(self, inte: Interaction):
        manager = RoleSelectorManager(self.database, inte.guild, inte.user)

        if self.database.execute(
                "SELECT COUNT(*) FROM TUTOR_ROLES_SELECTOR WHERE GUILD_ID=?;",
                (inte.guild_id,)
        ).fetchone()[0] >= 1:
            await manager.resend_delete(inte)

        else:
            await manager.add(inte)

    @app_commands.command(name="add_tutor_request", description="Add the tutor request message")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def add_tutor_request(
            self,
            inte: Interaction,
            message_channel: discord.TextChannel,
            tutor_request_channel: discord.TextChannel,
            tutor_accepted_channel: discord.TextChannel
    ):
        if self.database.execute(
                "SELECT COUNT(*) FROM TUTOR_REQUEST WHERE GUILD_ID=?;",
                (inte.guild_id,)
        ).fetchone()[0] >= 1:
            await inte.response.send_message(
                "A tutor request message is already set\nIn order to modify it, please remove it before",
                ephemeral=True
            )
            return

        msg = await send_tutor_request_message(message_channel)

        self.database.execute(
            "INSERT INTO TUTOR_REQUEST (REQ_MSG_ID,REQ_CHANNEL_ID,TUTOR_REQ_CHANNEL_ID,TUTOR_ACCEPT_CHANNEL_ID,"
            "GUILD_ID) VALUES (?,?,?,?,?);",
            (msg.id, message_channel.id, tutor_request_channel.id, tutor_accepted_channel.id, inte.guild_id)
        )
        self.database.commit()

        await inte.response.send_message(
            f"Successfully added a tutoring message in {message_channel.mention} which redirect requests into "
            f"{tutor_request_channel.mention}",
            ephemeral=True
        )

    @app_commands.command(name="remove_tutor_request", description="Add the tutor request message")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def remove_tutor_request(self, inte: Interaction):
        if self.database.execute(
                "SELECT COUNT(*) FROM TUTOR_REQUEST WHERE GUILD_ID=?;",
                (inte.guild_id,)
        ).fetchone()[0] == 0:
            await inte.response.send_message(
                "There is no tutor request messages on this guild",
                ephemeral=True
            )
            return

        await delete_tutor_request_message(self.database, inte.guild)

        self.database.execute(
            "DELETE FROM TUTOR_REQUEST WHERE GUILD_ID=?;",
            (inte.guild_id,)
        )
        self.database.commit()

        await inte.response.send_message(
            f"Successfully deleted this guild tutor request message",
            ephemeral=True
        )

    @app_commands.command(name="resend_tutor_request", description="Add the tutor request message")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def resend_tutor_request(self, inte: Interaction):
        if self.database.execute(
                "SELECT COUNT(*) FROM TUTOR_REQUEST WHERE GUILD_ID=?;",
                (inte.guild_id,)
        ).fetchone()[0] == 0:
            await inte.response.send_message(
                "There is no tutor request messages on this guild",
                ephemeral=True
            )
            return

        await delete_tutor_request_message(self.database, inte.guild)

        channel_id = self.database.execute(
            "SELECT REQ_CHANNEL_ID FROM TUTOR_REQUEST WHERE GUILD_ID=?;",
            (inte.guild_id,)
        ).fetchone()[0]

        msg = await send_tutor_request_message(inte.guild.get_channel(channel_id))

        self.database.execute(
            "UPDATE TUTOR_REQUEST SET REQ_MSG_ID=? WHERE GUILD_ID=?;",
            (msg.id, inte.guild_id)
        )
        self.database.commit()

        await inte.response.send_message(
            f"Successfully resent this guild tutor request message",
            ephemeral=True
        )

    @app_commands.command(name="manual", description="Send the module manual")
    @app_commands.default_permissions(administrator=True)
    @has_perm()
    async def manual(self, inte: Interaction):
        file = discord.File(
            "Cogs/TutorInsa/Documentation/Doc_LeBotLent_TutorINSA.pdf",
            filename="Doc_LeBotLent_TutorINSA.pdf"
        )
        await inte.response.send_message("Module TutorINSA manual:", file=file, ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, inte: discord.Interaction):
        if inte.type != InteractionType.component:
            return

        if "custom_id" not in inte.data.keys():
            return

        match inte.data["custom_id"]:
            case s if s.startswith("TUTORINSA.ROLESELECT."):
                await SelectorCallbacks(self.database).selector_year_callback(inte)

            case s if s.startswith("TUTORINSA.TUTOR_REQUEST_MODAL."):
                await tutor_request_callback(self.database, inte)

            case s if s.startswith("TUTORINSA.TUTOR_REQUEST_ACCEPT."):
                await TutorAcceptCallback(self.database).tutor_accept_callback(inte)


# === DO NOT REMOVE THE FOLLOWING OR CHANGE PARAMETERS === #

async def setup(bot: commands.AutoShardedBot, database: sqlite3.Connection):
    global PTR_DB

    PTR_DB.append(database)

    guilds = [discord.Object(id=i, type=discord.Guild) for i in get_config("TutorInsa.guilds")]
    await bot.add_cog(TutorInsa(bot, database), guilds=guilds)

# TODO: Voir document DM discord Tabatha (06/04) pour specification complètes

# DONE: Choix role par année / PO / spécialité => Register role for each in db

# DONE: Demande de tutorat (button + view)
# DONE: Quand un tutorat est demandé, message aux tuteurs (avec possibilité de l'accepter (bouton))

# (TODO: Moyen pour les tuteurs de marquer un tutorat qui leur a été assigné comme fait + donner le temps consacré + commentaires + autre séance?)
# (TODO: Demande d'avis anonyme automatisée après les tutorat (view))

# (TODO: Commande pour avoir un histoirque des tutorats demandés par une personne (+ le nombre))
# (TODO: La même chose pour les tuteurs pour voir quels tutorats ils ont fait / le temps)

# TODO: limit all actions to only tutorinsa discord => Already done for commands
# TODO: check config

# TODO: documentation pour passassion (p-e une commande pour la récupérer dispo aux respos + version pour les tuteurs)
# TODO: /manual

# TODO: perms + brief
