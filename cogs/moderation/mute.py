import discord
from discord.ext import commands
from datetime import timedelta
from discord.utils import utcnow

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="mute",
        description="Mute a member for a specified duration."
    )
    @discord.app_commands.describe(
        member="The member to mute",
        duration="Duration for the mute (e.g., '10m', '1h')",
        reason="Reason for the mute"
    )
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        """
        Mutes a member for a specified duration.
        """
        # Parse the duration
        time_multiplier = {'s': 1, 'm': 60, 'h': 3600}
        unit = duration[-1]
        if unit not in time_multiplier:
            await ctx.send("Invalid duration unit. Please use 's', 'm', or 'h'.", ephemeral=True)
            return

        try:
            time_amount = int(duration[:-1])
            mute_seconds = time_amount * time_multiplier[unit]
        except ValueError:
            await ctx.send("Invalid duration format. Please provide a number followed by 's', 'm', or 'h'.", ephemeral=True)
            return

        if mute_seconds > 2419200:  # Discord's maximum timeout limit is 28 days
            await ctx.send("Mute duration cannot exceed 28 days.", ephemeral=True)
            return

        try:
            # Use discord.utils.utcnow() for an aware datetime
            await member.timeout(utcnow() + timedelta(seconds=mute_seconds))
            embed = discord.Embed(
                title="Member Muted",
                description=f"{member.mention} has been muted for {duration}.",
                colour=0xff0000,
                timestamp=utcnow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text="Gooberbot")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I do not have permission to mute this member.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"Failed to mute member: {e}", ephemeral=True)

    @mute.error
    async def mute_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to mute members.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please mention a valid member and provide a valid duration.", ephemeral=True)
        else:
            await ctx.send(f"An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Mute(bot))