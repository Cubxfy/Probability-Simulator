import os
import sqlite3
import time
import discord
from discord.ext import commands
from discord import app_commands

# Constants for the daily reward
DAILY_AMOUNT = 100
DAILY_COOLDOWN = 86400  # 24 hours in seconds

class PointsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Path to the SQLite database file in the sqlite folder
        self.db_path = os.path.join("sqlite", "points.db")
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        # Create table for user points and daily claim timestamps
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_points (
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                last_daily INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        # Create table for guild configuration (like the mod role)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id TEXT PRIMARY KEY,
                mod_role_id TEXT
            )
        """)
        self.conn.commit()

    def get_user_data(self, guild_id: str, user_id: str):
        self.cursor.execute("SELECT points, last_daily FROM user_points WHERE guild_id=? AND user_id=?", (guild_id, user_id))
        result = self.cursor.fetchone()
        if result is None:
            # Insert default record if not found
            self.cursor.execute(
                "INSERT INTO user_points (guild_id, user_id, points, last_daily) VALUES (?, ?, 0, 0)",
                (guild_id, user_id)
            )
            self.conn.commit()
            return (0, 0)
        return result

    def update_user_points(self, guild_id: str, user_id: str, points: int):
        self.cursor.execute("UPDATE user_points SET points=? WHERE guild_id=? AND user_id=?", (points, guild_id, user_id))
        self.conn.commit()

    def update_last_daily(self, guild_id: str, user_id: str, timestamp: int):
        self.cursor.execute("UPDATE user_points SET last_daily=? WHERE guild_id=? AND user_id=?", (timestamp, guild_id, user_id))
        self.conn.commit()

    def get_mod_role(self, guild_id: str):
        # Open a new connection to the mod_config.db
        mod_config_db = os.path.join("sqlite", "mod_config.db")
        conn = sqlite3.connect(mod_config_db)
        cursor = conn.cursor()
        cursor.execute("SELECT mod_role_id FROM guild_config WHERE guild_id=?", (guild_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    @app_commands.command(name="points", description="Check your points or another user's points.")
    async def points(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user if user else interaction.user
        # If checking someone else's points, ensure the invoker has the mod role.
        if user and user != interaction.user:
            mod_role_id = self.get_mod_role(str(interaction.guild.id))
            if mod_role_id is None or int(mod_role_id) not in [r.id for r in interaction.user.roles]:
                await interaction.response.send_message("You do not have permission to view other users' points.", ephemeral=True)
                return
        current_points, _ = self.get_user_data(str(interaction.guild.id), str(target.id))
        # Using allowed_mentions to avoid sending a notification while keeping the mention clickable.
        allowed = discord.AllowedMentions(users=False)
        await interaction.response.send_message(
            f"{target.mention} has **{current_points}** points.", 
            ephemeral=False,
            allowed_mentions=allowed
        )

    @app_commands.command(name="addpoints", description="Add or remove points from a user.")
    async def add_points(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        # Only users with the mod role (set via /setmodrole) can use this command.
        mod_role_id = self.get_mod_role(str(interaction.guild.id))
        if mod_role_id is None or int(mod_role_id) not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        current_points, _ = self.get_user_data(str(interaction.guild.id), str(user.id))
        new_points = current_points + amount
        if new_points < 0:
            new_points = 0
        self.update_user_points(str(interaction.guild.id), str(user.id), new_points)
        allowed = discord.AllowedMentions(users=False)
        if amount >= 0:
            message = f"Added **{amount}** points to {user.mention}.\nThey now have **{new_points}** points."
        else:
            # Show the absolute value for removed points
            message = f"Removed **{abs(amount)}** points from {user.mention}.\nThey now have **{new_points}** points."
        await interaction.response.send_message(
            message,
            ephemeral=False,
            allowed_mentions=allowed
        )

    @app_commands.command(name="daily", description="Claim your daily points reward.")
    async def daily(self, interaction: discord.Interaction):
        now = int(time.time())
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        current_points, last_daily = self.get_user_data(guild_id, user_id)
        if now - last_daily >= DAILY_COOLDOWN:
            new_points = current_points + DAILY_AMOUNT
            self.update_user_points(guild_id, user_id, new_points)
            self.update_last_daily(guild_id, user_id, now)
            await interaction.response.send_message(
                f"You claimed your daily reward of **{DAILY_AMOUNT}** points! You now have **{new_points}** points.",
                ephemeral=True
            )
        else:
            remaining = DAILY_COOLDOWN - (now - last_daily)
            hrs = remaining // 3600
            mins = (remaining % 3600) // 60
            secs = remaining % 60
            await interaction.response.send_message(
                f"You have already claimed your daily reward. Time remaining until next claim: **{hrs}h {mins}m {secs}s**",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(PointsCog(bot))
