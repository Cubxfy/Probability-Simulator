import discord
from discord.ext import commands
from datetime import datetime  # Add this import

class Slowmode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="slowmode",
        description="Set the slowmode delay for the current channel."
    )
    @discord.app_commands.describe(
        time="Number of seconds or minutes for slowmode (0 to disable)",
        unit="Time unit: 'seconds', 'minutes', 's', or 'm'"
    )
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, time: int, unit: str = "seconds"):
        """
        Sets the slowmode delay for the current channel.
        """
        if time < 0:
            await ctx.send("Slowmode delay cannot be negative.", ephemeral=True)
            return

        # Normalize unit input
        unit = unit.lower()
        if unit in ["s", "seconds"]:
            unit = "seconds"
        elif unit in ["m", "minutes"]:
            unit = "minutes"
        else:
            await ctx.send("Invalid time unit. Please use 'seconds', 'minutes', 's', or 'm'.", ephemeral=True)
            return

        # Convert time to seconds if the unit is minutes
        if unit == "minutes":
            time *= 60

        if time > 21600:  # Discord's maximum slowmode limit is 6 hours
            await ctx.send("Slowmode delay cannot exceed 21600 seconds (6 hours).", ephemeral=True)
            return

        try:
            await ctx.channel.edit(slowmode_delay=time)
            if time == 0:
                embed = discord.Embed(
                    title="Slowmode Disabled",
                    description="Slowmode has been disabled for this channel.",
                    colour=0xffffff,
                    timestamp=datetime.now()
                )
            else:
                embed = discord.Embed(
                    title="Slowmode Established",
                    description=f"Slowmode has been enabled and set to: {time} seconds",
                    colour=0xffff00,
                    timestamp=datetime.now()
                )
            embed.set_footer(text="Gooberbot")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I do not have permission to manage this channel.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"Failed to set slowmode: {e}", ephemeral=True)

    @slowmode.error
    async def slowmode_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to manage channels.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid number of seconds or minutes.", ephemeral=True)
        else:
            await ctx.send(f"An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Slowmode(bot))