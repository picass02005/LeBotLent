# SPDX-License-Identifier: MIT
# Copyright (C) 2025 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

import sqlite3

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from GlobalModules.GetConfig import get_config


# === DO NOT CHANGE CLASS NAME OR __init__ PARAMETERS === #
class TutorInsa(commands.GroupCog):
    def __init__(self, bot: commands.AutoShardedBot, database: sqlite3.Connection):
        self.bot: bot = bot
        self.database = database

    @app_commands.command(name="test")
    @app_commands.default_permissions(administrator=True)
    async def test(self, interaction: Interaction):
        await interaction.response.send_message("test", ephemeral=True)


# === DO NOT REMOVE THE FOLLOWING OR CHANGE PARAMETERS === #

async def setup(bot: commands.AutoShardedBot, database: sqlite3.Connection):
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
