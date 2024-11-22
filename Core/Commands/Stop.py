import time

import discord
import psutil
from discord import ui, ButtonStyle
from discord.ext import commands


class Stop:
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.msg = None

    async def __button_callback(self, interaction: discord.Interaction):
        if self.ctx.author.id == interaction.user.id:
            await interaction.response.send_message("Bot stopping...", ephemeral=True)

            try:
                await self.msg.delete()

            except (discord.Forbidden, discord.NotFound, discord.HTTPException, AttributeError):
                pass

            exit(-1)

        else:
            await interaction.response.send_message(f"Only {self.ctx.author.display_name} can answer.", ephemeral=True)

    async def stop_command(self):
        button_yes = ui.Button(label="Yes", style=ButtonStyle.green)

        button_yes.callback = self.__button_callback

        view = ui.View()
        view.add_item(button_yes)

        self.msg = await self.ctx.send(
            f"Do you want to stop the bot? This instance is running since `"
            f"{time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(psutil.Process().create_time()))}`",
            view=view
        )
