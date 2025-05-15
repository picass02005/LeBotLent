# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import json
import sqlite3
import time
from typing import List, Tuple

import discord

from Cogs.TutorInsa.ConfirmSelect import ConfirmSelector
from Cogs.TutorInsa.Types.ClassEntry import ClassEntry
from GlobalModules.GetConfig import get_config
from GlobalModules.Logger import Logger


async def send_tutor_request_message(channel: discord.TextChannel) -> discord.Message:
    b = discord.ui.Button(
        style=discord.ButtonStyle.green,
        label="Demander un tutorat",
        custom_id=f"TUTORINSA.TUTOR_REQUEST_MODAL.{channel.id}"
    )
    v = discord.ui.View()
    v.add_item(b)

    e = discord.Embed(
        title="Demander une séance de tutorat / Request a tutoring session",
        description="### Afin de demander une séance de tutorat, veuillez suivre cette démarche:\n"
                    "1. Sélectionnez votre rôle de classe (si pas encore fait)\n"
                    "2. Appuyez sur le bouton ci-dessous, une fenêtre s'ouvrira\n"
                    "3. Remplissez les informations demandées\n"
                    "4. Cliquez sur \"Envoyer\"\n\n"
                    "### In order to request a tutoring session, please follow thoses steps:\n"
                    "1. Select your class role (if not already done)\n"
                    "2. Click on the button below, a window will be opened\n"
                    "3. Fill every fields accordingly\n"
                    "4. Click on \"Submit\"",
        color=get_config("core.base_embed_color")
    )

    msg = await channel.send(embed=e, view=v)
    return msg


async def delete_tutor_request_message(db: sqlite3.Connection, guild: discord.Guild):
    msg_id, channel_id = db.execute(
        "SELECT REQ_MSG_ID,REQ_CHANNEL_ID FROM TUTOR_REQUEST WHERE GUILD_ID = ?;",
        (guild.id,)
    ).fetchone()

    try:
        channel = guild.get_channel(channel_id)
        await channel.get_partial_message(msg_id).delete()

    except Exception as err:
        Logger(db).add_log("TUTORINSA", f"COULDN'T DELETE TUTOR REQUEST MESSAGE: {type(err)}: {err}")


async def tutor_request_callback(db: sqlite3.Connection, inte: discord.Interaction):
    classes = db.execute(
        "SELECT ROLE_ID,CLASS FROM TUTOR_ROLES WHERE GUILD_ID=?;",
        (inte.guild_id,)
    ).fetchall()

    roles_id = [i.id for i in inte.user.roles]
    common_classes = [i for i in classes if i[0] in roles_id]

    if len(common_classes) != 1:
        c = db.execute(
            "SELECT MESSAGE_ID,CHANNEL_ID FROM TUTOR_ROLES_SELECTOR WHERE GUILD_ID=?;",
            (inte.guild_id,)
        ).fetchone()

        if c is None:
            await inte.response.send_message(
                "Aucun message de sélection de classe n'est défini, merci de contacter les administrateurs du serveur."
                "\n\nNo role selection message defined, please contact guild admins.",
                ephemeral=True
            )
            return

        msg = inte.guild.get_channel(c[1]).get_partial_message(c[0])
        if len(common_classes) == 0:
            await inte.response.send_message(
                f"Pour pouvoir demander un tutorat, merci de sélectionner votre classe dans {msg.jump_url}\n\n"
                f"In order to ask for a tutoring session, please select your class in {msg.jump_url}",
                ephemeral=True
            )
            return

        else:
            await inte.response.send_message(
                f"Vous avez plusieurs roles de classes. Pour pouvoir demander un tutorat, merci de sélectionner "
                f"votre classe actuelle dans {msg.jump_url}\n\n"
                f"You have multiple class roles. In order to ask for a tutoring session, please select your current "
                f"class in {msg.jump_url}",
                ephemeral=True
            )
            return

    await inte.response.send_modal(RequestTutoringModal(db, common_classes[0][1]))


class RequestTutoringModal(discord.ui.Modal):
    subject = discord.ui.TextInput(
        label="Matière / Academic subject",
        style=discord.TextStyle.short,
        placeholder="Mathématiques / mathematics",
        required=True,
        max_length=100
    )

    concepts = discord.ui.TextInput(
        label="Notions à revoir / Concepts to review",
        style=discord.TextStyle.paragraph,
        placeholder="Leçon sur la dérivabilité\n\n"
                    "Lesson about derivatives",
        required=True,
        max_length=1024
    )

    contact = discord.ui.TextInput(
        label="Votre contact / Your contact",
        style=discord.TextStyle.paragraph,
        placeholder="Email: example@insa-toulouse.fr\nInstagram: @example\nMessenger: example\n...",
        required=True,
        max_length=1024
    )

    def __init__(self, database: sqlite3.Connection, class_id: str):
        super().__init__(title="Demande de tutorat / Request tutoring session")
        self.db = database
        self.class_id = class_id

    async def on_submit(self, inte: discord.Interaction, /) -> None:
        tutor_channel_id: None | Tuple[int] = self.db.execute(
            "SELECT TUTOR_REQ_CHANNEL_ID FROM TUTOR_REQUEST WHERE GUILD_ID=?;",
            (inte.guild_id,)
        ).fetchone()

        err: None | str = None

        if tutor_channel_id is None:
            err = "Unable to find tutor channel in db"

        else:
            tutor_channel = await inte.guild.fetch_channel(tutor_channel_id[0])

            if tutor_channel is None:
                err = f"Couldn't get channel object (ID: {tutor_channel_id})"

            else:
                try:
                    await self.send_tutor_message(tutor_channel, inte.user)

                except Exception as e:
                    err = f"An error happened while sending message: [{type(e)}] {e}"

        if err is not None:
            Logger(self.db).add_log(
                "TUTORINSA",
                f"Couldn't forward tutoring session request: {err}"
            )

            e = discord.Embed(
                title="ERREUR / ERROR",
                description="Une erreur est survenue, votre demande de tutorat n'a pas aboutie.\n"
                            "### Merci de contacter un administrateur du serveur.\n\n"
                            "An error happened, your tutoring session request did not succeed.\n"
                            "### Please contact a guild administrator.",
                color=0xFF0000
            )

            await inte.response.send_message(embed=e, ephemeral=True)

        else:
            e = discord.Embed(
                title="Succès / Success",
                description="### Votre demande de tutorat à été transmise.\n"
                            "Un tuteur vous recontactera dans les plus brefs délais.\n\n"
                            "### Your tutoring session has been forwarded.\n"
                            "A tutor will contact you as soon as possible.",
                color=0x00FF00
            )

            await inte.response.send_message(embed=e, ephemeral=True)

    async def send_tutor_message(self, channel: discord.TextChannel, author: discord.User):
        with open("Cogs/TutorInsa/Config/classes.json", "r") as f:
            class_entry = ClassEntry(json.loads(f.read())[self.class_id])

        mentions = self.mentions(class_entry, channel.guild)

        e = discord.Embed(
            title="Nouvelle demande de tutorat",
            description="Les informations nécessaires sont disponibles ci-dessous",
            color=get_config("core.base_embed_color")
        )

        e.add_field(
            name="Identité",
            value=f"Auteur: {author.mention}\n"
                  f"Année: `{class_entry.year}A`\n"
                  f"Classe: `{class_entry.name}`",
            inline=True
        )

        e.add_field(
            name="Matière",
            value=self.subject.value,
            inline=True
        )

        e.add_field(
            name="Notions demandées",
            value=self.concepts.value,
            inline=False
        )

        e.add_field(
            name="Contact",
            value=self.contact.value,
            inline=False
        )

        button = discord.ui.Button(
            label="Accepter le tutorat",
            style=discord.ButtonStyle.green,
            custom_id=f"TUTORINSA.TUTOR_REQUEST_ACCEPT.{hash(f"{author.id}.{time.time()}")}"
        )
        view = discord.ui.View()
        view.add_item(button)

        await channel.send(content=f"Mentions: {mentions}", embed=e, view=view)

    def mentions(self, class_entry: ClassEntry, guild: discord.Guild) -> str:
        args: List[str | int] = class_entry.next
        args.append(guild.id)

        from_db: List[Tuple[int]] = self.db.execute(
            f"SELECT ROLE_ID FROM TUTOR_ROLES WHERE CLASS IN ({','.join(['?'] * (len(class_entry.next) - 1))}) AND "
            f"GUILD_ID=?;",
            tuple(args)
        ).fetchall()

        if len(from_db) == 0 or len(class_entry.next) == 0:
            return "`Aucun role à mentionner trouvés`"

        return " ".join([f"<@&{i[0]}>" for i in from_db])


class TutorAcceptCallback:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.original_message: None | discord.Message = None

    async def tutor_accept_callback(self, inte: discord.Interaction):
        v = discord.ui.View()
        v.add_item(ConfirmSelector(inte.user, self.tutor_forward_message))

        self.original_message = inte.message

        await inte.response.send_message("Voulez-vous accepter ce tutorat?", view=v, ephemeral=True)

    async def tutor_forward_message(self, inte: discord.Interaction):
        accept_chanel_id = self.db.execute(
            "SELECT TUTOR_ACCEPT_CHANNEL_ID FROM TUTOR_REQUEST WHERE GUILD_ID=?;",
            (inte.guild_id,)
        ).fetchone()

        err: None | str = None
        accept_channel: None | discord.TextChannel = None

        if accept_chanel_id is None:
            err = "Couldn't fetch TUTOR_ACCEPT_CHANNEL_ID from DB"

        else:
            try:
                accept_channel = await inte.guild.fetch_channel(accept_chanel_id[0])

            except Exception as e:
                err = f"Couldn't fetch channel with ID {accept_chanel_id[0]}: {type(e)} {e}"

        if err is not None:
            Logger(self.db).add_log(
                "TUTORINSA",
                f"An error occured while accepting a tutor request: {err}"
            )

            await inte.followup.send(
                "Une erreur s'est produite. Merci de contacter les administrateurs du serveur.",
                ephemeral=True
            )
            return

        e = self.original_message.embeds[0]
        e.title = "Tutorat pris en charge"

        await accept_channel.send(
            content=f"# Tutorat pris en charge par {inte.user.mention}",
            embed=e
        )

        try:
            await self.original_message.delete()
            await inte.followup.send("Tutorat accepté avec succès", ephemeral=True)

        except Exception:
            await inte.followup.send(
                "Tutorat accepté avec une erreur lors de la suppression de sa demande.\n"
                "Un message à été envoyé pour prévenir les autres tuteurs.",
                ephemeral=True
            )

            await inte.followup.send(
                f"Une erreur s'est produite lors de la suppression de la demande de tutorat suivante: "
                f"{self.original_message.jump_url}"
            )
