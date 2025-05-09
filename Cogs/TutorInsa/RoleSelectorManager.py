# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import json
import sqlite3
from typing import List, Dict, Tuple

import discord
from discord import Interaction, ButtonStyle

from Cogs.TutorInsa.ConfirmSelect import ConfirmSelector
from Cogs.TutorInsa.Types.ClassEntry import ClassEntry
from GlobalModules.GetConfig import get_config
from GlobalModules.Logger import Logger


class RoleSelectorManager:
    def __init__(self, db: sqlite3.Connection, guild: discord.Guild, author: discord.Member):
        self.db: sqlite3.Connection = db
        self.guild: discord.Guild = guild
        self.author: discord.Member = author

    async def add(self, inte: Interaction):
        v = discord.ui.View()
        v.add_item(ConfirmSelector(inte.user, self.add_callback))

        await inte.response.send_message(
            "Are you sure you want to add a role selector in this channel?",
            view=v,
            ephemeral=True
        )

    async def add_callback(self, inte: Interaction) -> None:
        msg = await self.send_message(inte.channel)

        self.db.execute(
            "INSERT INTO TUTOR_ROLES_SELECTOR (MESSAGE_ID,CHANNEL_ID,GUILD_ID) VALUES (?,?,?);",
            (msg.id, inte.channel_id, inte.guild_id)
        )
        self.db.commit()

        await inte.followup.send("Successfully added this role selector", ephemeral=True)

    async def resend_delete(self, inte: Interaction):
        b_resend = discord.ui.Button(
            label="Resend",
            style=ButtonStyle.green
        )
        b_resend.callback = self.resend_callback

        b_delete = discord.ui.Button(
            label="Delete",
            style=ButtonStyle.red
        )
        b_delete.callback = self.delete_callback

        b_cancel = discord.ui.Button(
            label="Cancel",
            style=ButtonStyle.blurple
        )
        b_cancel.callback = self.cancel_callback

        v = discord.ui.View()
        v.add_item(b_resend)
        v.add_item(b_delete)
        v.add_item(b_cancel)

        e = discord.Embed(
            title="Manage current role message",
            description="Select one action to perform",
            color=get_config("core.base_embed_color")
        )

        await inte.response.send_message(embed=e, view=v, ephemeral=True)

    async def resend_callback(self, inte: Interaction):
        if inte.user.id != self.author.id:
            await inte.response.send_message("You do not have permission to interact here", ephemeral=True)
            return

        try:
            channel_id: int = self.db.execute(
                "SELECT CHANNEL_ID FROM TUTOR_ROLES_SELECTOR WHERE GUILD_ID=?;",
                (inte.guild_id,)
            ).fetchone()[0]

            channel: discord.TextChannel = await inte.guild.fetch_channel(channel_id)

            await self.delete_actual_message(inte.guild)
            msg = await self.send_message(channel)

            self.db.execute(
                "INSERT INTO TUTOR_ROLES_SELECTOR (MESSAGE_ID,CHANNEL_ID,GUILD_ID) VALUES (?,?,?);",
                (msg.id, channel_id, inte.guild_id)
            )
            self.db.commit()

            await inte.response.send_message("Message resent successfully", ephemeral=True)

        except Exception as err:
            await inte.response.send_message(
                "Couldn't resend message\nTry to delete it first using this command then send it again\n"
                "If this issue persists, please contact the developer",
                ephemeral=True
            )

            Logger(self.db).add_log("TUTORINSA", f"Couldn't resend message: {type(err)}: {err}")

    async def delete_callback(self, inte: Interaction):
        if inte.user.id != self.author.id:
            await inte.response.send_message("You do not have permission to interact here", ephemeral=True)
            return

        await inte.response.send_message("Delete", ephemeral=True)

    async def cancel_callback(self, inte: Interaction):
        if inte.user.id != self.author.id:
            await inte.response.send_message("You do not have permission to interact here", ephemeral=True)
            return

        await inte.response.send_message("Cancelled", ephemeral=True)

    @staticmethod
    async def send_message(channel: discord.TextChannel) -> discord.Message:
        years = []
        with open("Cogs/TutorInsa/Config/classes.json", "r") as f:
            for i in json.loads(f.read()).values():
                c = ClassEntry(i)
                if c.year not in years:
                    years.append(c.year)

        years.sort()

        view = discord.ui.View(timeout=None)
        view.add_item(
            discord.ui.Select(
                custom_id=f"TUTORINSA.ROLESELECT.{channel.id}",
                placeholder="Sélectionnez votre année / Select your year",
                options=[discord.SelectOption(label=f"{i}A", value=i) for i in years]
            )
        )

        e = discord.Embed(
            title="Sélectionnez votre classe / Select your class",
            description="Afin de sélectionner votre classe, vous devez d'abord sélectionner votre année ci-dessous\n\n"
                        "In order to select your class, please select your current year below",
            color=get_config("core.base_embed_color")
        )

        return await channel.send(embed=e, view=view)

    async def delete_actual_message(self, guild: discord.Guild):
        tmp: Tuple[int, int] | None = self.db.execute(
            "SELECT MESSAGE_ID, CHANNEL_ID FROM TUTOR_ROLES_SELECTOR WHERE GUILD_ID=?;",
            (guild.id,)
        ).fetchone()

        actual_channel: discord.TextChannel = guild.get_channel(tmp[1])

        if actual_channel is not None:
            actual_msg: discord.PartialMessage = actual_channel.get_partial_message(tmp[0])
            try:
                await actual_msg.delete()

            except (discord.NotFound, discord.Forbidden):
                pass

        self.db.execute("DELETE FROM TUTOR_ROLES_SELECTOR WHERE GUILD_ID=?;", (guild.id,))
        self.db.commit()


class SelectorCallbacks:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    async def selector_year_callback(self, inte: discord.Interaction):
        """
        Called on global message when selecting year
        :param inte: The returned interaction
        :return: None
        """

        year: int = int(inte.data['values'][0])

        from_json: Dict[str: ClassEntry] = dict()
        with open("Cogs/TutorInsa/Config/classes.json", "r") as f:
            for k, v in json.loads(f.read()).items():
                c: ClassEntry = ClassEntry(v)
                if c.year == year:
                    from_json.update({k: c})

        from_db: List[Tuple[str]] = self.db.execute(
            f"SELECT CLASS FROM TUTOR_ROLES WHERE CLASS IN ({','.join(['?'] * len(from_json))});",
            list(from_json.keys())
        ).fetchall()

        options = []

        for i in from_db:
            c: ClassEntry = from_json[i[0]]
            options.append(discord.SelectOption(
                label=c.name,
                value=f"{i[0]}",
                description=f"Vous donne le role associé à cette classe / Gives yourself the role linked to this class"
            ))

        if options:
            select = discord.ui.Select(placeholder="Sélectionnez votre classe / Select your class", options=options)
            select.callback = self.selector_class_callback

            view = discord.ui.View()
            view.add_item(select)

            e = discord.Embed(
                title="Sélectionnez votre classe / Select your class",
                description="Merci de sélectionner votre classe ci-dessous\n"
                            "Si celle-ci n'apparait pas, merci de contacter les propriétaires du serveur\n\n"
                            "Please select your class below\n"
                            "If it doesn't show, please contact the owners of this guild",
                color=get_config("core.base_embed_color")
            )

            await inte.response.send_message(embed=e, view=view, ephemeral=True)  # TODO

        else:
            e = discord.Embed(
                title="Erreur / Error",
                description=f"Il n'y a pas de roles associés pour l'année `{year}A`\n"
                            f"Merci de contacter un propriétaire du serveur.\n\n"
                            f"There are no role linked to year `{year}A`\n"
                            f"Please contact an owner of this guild.",
                color=0xFF0000
            )

            await inte.response.send_message(
                embed=e,
                ephemeral=True
            )

    async def selector_class_callback(self, inte: discord.Interaction):
        """
        Called on ephemeral message when selecting class
        :param inte: The returned interaction
        :return: None
        """

        class_id: str = inte.data['values'][0]

        to_add_id = self.db.execute(
            "SELECT ROLE_ID FROM TUTOR_ROLES WHERE GUILD_ID=? AND CLASS=?;",
            (inte.guild_id, class_id)
        ).fetchone()[0]

        args = [inte.guild_id]
        args.extend([i.id for i in inte.user.roles])

        to_del_id = [i[0] for i in self.db.execute(
            f"SELECT ROLE_ID FROM TUTOR_ROLES WHERE GUILD_ID=? AND ROLE_ID IN "
            f"({','.join(['?'] * len(inte.user.roles))});",
            tuple(args)
        ).fetchall()]

        if to_add_id in to_del_id:
            to_del_id.remove(to_add_id)

        else:
            await inte.user.add_roles(inte.guild.get_role(to_add_id), reason="TutorInsa class role selector")

        if to_del_id:
            to_del = [inte.guild.get_role(i) for i in to_del_id]
            await inte.user.remove_roles(*tuple(to_del), reason="TutorInsa class role selector")

        with open("Cogs/TutorInsa/Config/classes.json", "r") as f:
            c: ClassEntry = ClassEntry(json.loads(f.read())[class_id])

        e = discord.Embed(
            title="Succès / Success",
            description=f"Sélection du role lié à la classe `{c.name}` réalisée avec succès\n\n"
                        f"Successfully selected role linked to class `{c.name}`",
            color=get_config("core.base_embed_color")
        )

        await inte.response.send_message(
            embed=e,
            ephemeral=True
        )
