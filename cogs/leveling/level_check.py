import discord
from discord.ext import commands
import sqlite3

class LevelCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('levels.db')
        self.cursor = self.conn.cursor()

    def cog_unload(self):
        self.conn.close()

    @commands.hybrid_command(
        name="level",
        description="Check the level and XP of a member."
    )
    @discord.app_commands.describe(member="The member whose level you want to check")
    async def level(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        guild_id = ctx.guild.id

        self.cursor.execute('SELECT xp, level FROM levels WHERE guild_id = ? AND user_id = ?', (guild_id, member.id))
        result = self.cursor.fetchone()

        if result:
            xp, level = result
            required_xp = self.calculate_required_xp(level + 1)
            xp_to_next = required_xp - xp
            embed = discord.Embed(
                title=f"{member.name}'s Level",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.add_field(name="Level", value=str(level), inline=True)
            embed.add_field(name="XP", value=f"{xp} / {required_xp}", inline=True)
            embed.add_field(name="XP to Next Level", value=str(xp_to_next), inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{member.mention} has not earned any XP yet.")

    def calculate_required_xp(self, level):
        return 100 * (level ** 2)

    @level.error
    async def level_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Please mention a valid member or provide a valid user ID.", ephemeral=True)
        else:
            await ctx.send(f"An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(LevelCheck(bot))