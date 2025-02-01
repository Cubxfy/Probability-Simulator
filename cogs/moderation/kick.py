import discord
from discord.ext import commands
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="kick",
        description="Kick a member from the server."
    )
    @discord.app_commands.describe(
        member="The member to kick",
        reason="Reason for the kick"
    )
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """
        Kicks a member from the server.
        """
        try:
            await member.kick(reason=reason)
            logger.info(f"Kicked {member} from guild {ctx.guild.id} for reason: {reason}")
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} has been kicked from the server.",
                colour=0xff0000
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text="Gooberbot")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I do not have permission to kick this member.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"Failed to kick member: {e}", ephemeral=True)

    @kick.error
    async def kick_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to kick members.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please mention a valid member to kick.", ephemeral=True)
        else:
            await ctx.send(f"An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Kick(bot))