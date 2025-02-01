import discord
from discord.ext import commands
import sqlite3
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('warnings.db')
        self.cursor = self.conn.cursor()
        
        # Create table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                warn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
        
        # Verify if 'warn_id' and 'timestamp' columns exist, and add them if they don't
        self.cursor.execute("PRAGMA table_info(warnings)")
        columns = [info[1] for info in self.cursor.fetchall()]
        
        if 'warn_id' not in columns:
            try:
                self.cursor.execute("ALTER TABLE warnings ADD COLUMN warn_id INTEGER PRIMARY KEY AUTOINCREMENT")
                self.conn.commit()
                logger.info("Added 'warn_id' column to 'warnings' table.")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not add 'warn_id' column: {e}")
        
        if 'timestamp' not in columns:
            try:
                self.cursor.execute("ALTER TABLE warnings ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP")
                self.conn.commit()
                logger.info("Added 'timestamp' column to 'warnings' table.")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not add 'timestamp' column: {e}")

    @commands.hybrid_command(name="warn", description="Warn a member for a specified reason.")
    @discord.app_commands.describe(member="The member to warn", reason="Reason for the warning")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        try:
            guild_id = ctx.guild.id
            self.cursor.execute(
                'INSERT INTO warnings (guild_id, user_id, reason) VALUES (?, ?, ?)',
                (guild_id, member.id, reason)
            )
            self.conn.commit()
            logger.info(f"Warned {member} in guild {guild_id} for reason: {reason}")
            await ctx.send(f'{member.mention} has been warned for: {reason}')
        except Exception as e:
            logger.error(f"Error in warn command: {e}")
            await ctx.send("An error occurred while issuing the warning. Please try again later.")

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use this command.")

    @commands.hybrid_command(name="warns", description="Show warnings for a specified member.")
    @discord.app_commands.describe(member="The member whose warnings you want to check")
    async def warns(self, ctx: commands.Context, member: discord.Member):
        try:
            guild_id = ctx.guild.id
            self.cursor.execute(
                'SELECT warn_id, timestamp, reason FROM warnings WHERE guild_id = ? AND user_id = ?',
                (guild_id, member.id)
            )
            results = self.cursor.fetchall()

            if results:
                embed = discord.Embed(
                    title=f"Warns for: {member}",
                    description=f"User ID: {member.id}",
                    colour=0xff0000,
                    timestamp=datetime.utcnow()
                )
                for warn in results:
                    warn_id, timestamp, reason = warn
                    try:
                        # Attempt to parse the timestamp
                        warn_datetime = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                        date_str = warn_datetime.strftime("%Y-%m-%d")
                        time_str = warn_datetime.strftime("%H:%M:%S")
                    except ValueError:
                        # If parsing fails, use the raw timestamp
                        date_str = "Unknown Date"
                        time_str = "Unknown Time"
                        logger.warning(f"Failed to parse timestamp: {timestamp} for warn_id: {warn_id}")

                    embed.add_field(
                        name=f"Warning ID: {warn_id}",
                        value=f"**Date:** {date_str}\n**Time:** {time_str}\n**Reason:** {reason}",
                        inline=False
                    )
                embed.set_footer(text="Gooberbot", icon_url="https://slate.dan.onl/slate.png")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"{member.mention} has no warnings in this server.")
        except Exception as e:
            logger.error(f"Error in warns command: {e}")
            await ctx.send("An error occurred while fetching warnings. Please try again later.")

    @commands.hybrid_command(name="remove_warn", description="Remove a specific warning from a member.")
    @discord.app_commands.describe(member="The member whose warning you want to remove", warn_id="The ID of the warning to remove")
    @commands.has_permissions(manage_messages=True)
    async def remove_warn(self, ctx: commands.Context, member: discord.Member, warn_id: int):
        try:
            guild_id = ctx.guild.id
            # Check if the warning exists
            self.cursor.execute(
                'SELECT reason FROM warnings WHERE guild_id = ? AND user_id = ? AND warn_id = ?',
                (guild_id, member.id, warn_id)
            )
            result = self.cursor.fetchone()

            if result:
                reason = result[0]
                # Delete the warning
                self.cursor.execute(
                    'DELETE FROM warnings WHERE guild_id = ? AND user_id = ? AND warn_id = ?',
                    (guild_id, member.id, warn_id)
                )
                self.conn.commit()
                logger.info(f"Removed warn_id {warn_id} for {member} in guild {guild_id}. Reason was: {reason}")
                await ctx.send(f"Successfully removed warning ID `{warn_id}` for {member.mention}.")
            else:
                await ctx.send(f"No warning found with ID `{warn_id}` for {member.mention}.")
        except Exception as e:
            logger.error(f"Error in remove_warn command: {e}")
            await ctx.send("An error occurred while removing the warning. Please try again later.")

    @remove_warn.error
    async def remove_warn_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to remove warnings.")

    @commands.hybrid_command(name="clear_warns", description="Remove all warnings from a member.")
    @discord.app_commands.describe(member="The member whose warnings you want to clear")
    @commands.has_permissions(manage_messages=True)
    async def clear_warns(self, ctx: commands.Context, member: discord.Member):
        try:
            guild_id = ctx.guild.id
            # Check if the member has any warnings
            self.cursor.execute(
                'SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?',
                (guild_id, member.id)
            )
            count = self.cursor.fetchone()[0]

            if count > 0:
                # Delete all warnings
                self.cursor.execute(
                    'DELETE FROM warnings WHERE guild_id = ? AND user_id = ?',
                    (guild_id, member.id)
                )
                self.conn.commit()
                logger.info(f"Cleared all {count} warnings for {member} in guild {guild_id}.")
                await ctx.send(f"Successfully cleared all `{count}` warnings for {member.mention}.")
            else:
                await ctx.send(f"{member.mention} has no warnings to clear.")
        except Exception as e:
            logger.error(f"Error in clear_warns command: {e}")
            await ctx.send("An error occurred while clearing warnings. Please try again later.")

    @clear_warns.error
    async def clear_warns_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to clear warnings.")

    def cog_unload(self):
        self.conn.close()

async def setup(bot):
    await bot.add_cog(Warn(bot))