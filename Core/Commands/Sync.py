from discord.ext import commands

from GlobalModules.Logger import Logger


async def sync_command(bot: commands.AutoShardedBot, logger: Logger, ctx: commands.Context, guild_only: bool = False):
    async with ctx.typing():
        if guild_only:
            if ctx.guild is None:
                await ctx.send("Couldn't retrieve the guild information")

            else:
                await bot.tree.sync(guild=ctx.guild)
                logger.add_log(
                    "Sync",
                    f"Successfully synced commands tree for {ctx.guild.name} (id: {ctx.guild.id})"
                )

                await ctx.send("Successfully synced this guild commands tree")

        else:
            await bot.tree.sync()
            logger.add_log("Sync", "Successfully synced global commands tree")

            await ctx.send("Successfully synced global commands tree")
