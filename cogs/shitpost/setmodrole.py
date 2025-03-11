import os
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands

class SetModRoleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Connect to the same SQLite database as the points system
        self.db_path = os.path.join("sqlite", "mod_config.db")
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        # Create the guild configuration table if it doesn't exist
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id TEXT PRIMARY KEY,
                mod_role_id TEXT
            )
        """)
        self.conn.commit()

    def set_mod_role(self, guild_id: str, role_id: str):
        self.cursor.execute(
            "INSERT OR REPLACE INTO guild_config (guild_id, mod_role_id) VALUES (?, ?)",
            (guild_id, role_id)
        )
        self.conn.commit()

    @app_commands.command(name="setmodrole", description="Designate a role for moderator-only functions.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_mod_role_command(self, interaction: discord.Interaction, role: discord.Role):
        self.set_mod_role(str(interaction.guild.id), str(role.id))
        await interaction.response.send_message(f"Mod role set to {role.mention}", ephemeral=False)

    @set_mod_role_command.error
    async def set_mod_role_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SetModRoleCog(bot))
