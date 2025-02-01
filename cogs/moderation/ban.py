import discord
from discord.ext import commands
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ban",
        description="Ban a member from the server."
    )
    @discord.app_commands.describe(
        member="The member to ban",
        reason="Reason for the ban"
    )
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """
        Bans a member from the server.
        """
        try:
            await member.ban(reason=reason)
            logger.info(f"Banned {member} from guild {ctx.guild.id} for reason: {reason}")
            embed = discord.Embed(
                title="Member Banned",
                description=f"{member.mention} has been banned from the server.",
                colour=0xff0000
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text="Gooberbot")
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I do not have permission to ban this member.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"Failed to ban member: {e}", ephemeral=True)

    @ban.error
    async def ban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to ban members.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please mention a valid member to ban.", ephemeral=True)
        else:
            await ctx.send(f"An error occurred: {error}", ephemeral=True)

    @commands.hybrid_command(
        name="unban",
        description="Unban a user from the server using their User ID."
    )
    @discord.app_commands.describe(
        user_id="The User ID of the member to unban",
        reason="Reason for the unban"
    )
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user_id: str, *, reason: str = "No reason provided"):
        """
        Unbans a user from the server using their User ID.
        """
        try:
            user_id = int(user_id)  # Ensure user_id is treated as an integer
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            logger.info(f"Unbanned {user} from guild {ctx.guild.id} for reason: {reason}")
            embed = discord.Embed(
                title="Member Unbanned",
                description=f"{user.mention} has been unbanned from the server.",
                colour=0x00ff00
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text="Gooberbot")
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send("Invalid User ID format. Please provide a valid User ID.", ephemeral=True)
        except discord.NotFound:
            await ctx.send("User not found in the ban list.", ephemeral=True)
        except discord.Forbidden:
            await ctx.send("I do not have permission to unban this user.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"Failed to unban user: {e}", ephemeral=True)

    @unban.error
    async def unban_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to unban members.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please provide a valid User ID to unban.", ephemeral=True)
        else:
            await ctx.send(f"An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Ban(bot))