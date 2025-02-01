import discord
from discord.ext import commands
import random
import sqlite3

# Initialize bot with all intents
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# High-Low game buttons with streak tracking
class Buttons(discord.ui.View):
    def __init__(self, user_id, cog):
        super().__init__()
        self.random_number = random.randint(1, 100)
        self.count = 0
        self.highest = cog.get_highest_streak(user_id)  # Retrieve the user's highest streak
        self.user_id = user_id
        self.cog = cog  # Reference to highlowCog for database updates

    async def update_streak(self, interaction, result):
        if result == "Correct":
            self.count += 1
        else:
            self.cog.update_highest_streak(self.user_id, self.count)  # Save highest streak
            self.count = 0  # Reset streak on incorrect answer

        self.random_number = random.randint(1, 100)  # Generate new number
        await interaction.response.edit_message(
            content=f"{result}\nCurrent Streak: {self.count}\nHighest Streak: {self.highest}\nNew number: {self.random_number}",
            view=self
        )

    @discord.ui.button(label="Higher", style=discord.ButtonStyle.grey)
    async def button_higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Higher Button Clicked")
        result = "Correct" if random.randint(1, 100) > self.random_number else "Incorrect"
        await self.update_streak(interaction, result)

    @discord.ui.button(label="Lower", style=discord.ButtonStyle.grey)
    async def button_lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Lower Button Clicked")
        result = "Correct" if random.randint(1, 100) < self.random_number else "Incorrect"
        await self.update_streak(interaction, result)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.grey)
    async def button_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Close Button Clicked")
        self.cog.update_highest_streak(self.user_id, self.count)  # Save streak before ending
        await interaction.response.edit_message(content="**Game ended.**", view=None)

# High-Low Game Cog (Handles Database)
class highlowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("streaks.db")  # Connect to database
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS streaks (
                user_id INTEGER PRIMARY KEY,
                highest_streak INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def get_highest_streak(self, user_id):
        """Retrieve the highest streak of a user from the database."""
        self.cursor.execute("SELECT highest_streak FROM streaks WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0  # Return highest streak or 0 if user is not found

    def update_highest_streak(self, user_id, new_streak):
        """Update the user's highest streak in the database."""
        current_highest = self.get_highest_streak(user_id)
        if new_streak > current_highest:
            self.cursor.execute("""
                INSERT INTO streaks (user_id, highest_streak)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET highest_streak = ?
            """, (user_id, new_streak, new_streak))
            self.conn.commit()

    @commands.hybrid_command(aliases=["hl"])  # Allows both !hl and !highlow
    async def highlow(self, ctx):
        """Start a High-Low game."""
        user_id = ctx.author.id
        view = Buttons(user_id, self)
        await ctx.reply(f"Starting number: {view.random_number}\nHighest Streak: {view.highest}", view=view)

async def setup(bot):
    await bot.add_cog(highlowCog(bot))