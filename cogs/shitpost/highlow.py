import os
import random
import asyncio
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands

# Constants
DEFAULT_BET = 10
MIN_BET = 10
DB_PATH = os.path.join("sqlite", "points.db")

# Helper functions to interact with the sqlite database.
def get_user_data(guild_id: str, user_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT points, last_daily FROM user_points WHERE guild_id=? AND user_id=?", (guild_id, user_id))
    result = cursor.fetchone()
    if result is None:
        cursor.execute("INSERT INTO user_points (guild_id, user_id, points, last_daily) VALUES (?, ?, 0, 0)",
                       (guild_id, user_id))
        conn.commit()
        conn.close()
        return (0, 0)
    conn.close()
    return result

def update_user_points(guild_id: str, user_id: str, points: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE user_points SET points=? WHERE guild_id=? AND user_id=?", (points, guild_id, user_id))
    conn.commit()
    conn.close()

# Modal for changing the bet amount.
class ChangeBetModal(discord.ui.Modal, title="Change Bet Amount"):
    bet = discord.ui.TextInput(
        label="Enter your new bet (minimum 10)",
        placeholder="e.g. 50",
        required=True,
    )

    def __init__(self, view: "HighLowView"):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            new_bet = int(self.bet.value)
        except ValueError:
            await interaction.response.send_message("Please enter a valid integer.", ephemeral=True)
            return

        if new_bet < MIN_BET:
            await interaction.response.send_message(f"Bet must be at least {MIN_BET}.", ephemeral=True)
            return

        self.view.bet = new_bet
        # Update embed with the new bet
        self.view.embed.description = f"Cost to play: **{self.view.bet}** points"
        await self.view.message.edit(embed=self.view.embed, view=self.view)
        await interaction.response.send_message(f"Bet updated to **{self.view.bet}** points.", ephemeral=True)

# The main view for the game
class HighLowView(discord.ui.View):
    def __init__(self, author: discord.User, bet: int = DEFAULT_BET):
        super().__init__(timeout=120)  # Timeout in seconds
        self.author = author
        self.bet = bet
        self.message = None  # Will store the message after sending.
        # Initial embed showing the game
        self.embed = discord.Embed(title="Highlow", color=discord.Color.blue())
        self.random_number = random.randint(1, 100)
        self.embed.add_field(name="Number",value=f"{self.random_number}", inline=False)
        self.embed.description = f"Cost to play: **{self.bet}** points"


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only the original caller may interact.
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="Higher", style=discord.ButtonStyle.grey)
    async def button_higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        #defer the message
        await interaction.response.defer()

        #check if playable
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        current_points, _ = get_user_data(guild_id, user_id)
        if current_points < self.bet:
            await interaction.followup.send("You do not have enough points to play.", ephemeral=True)
            return

        # Deduct the bet immediately.
        new_points = current_points - self.bet
        update_user_points(guild_id, user_id, new_points)

        print("Higher Button Clicked")
        new_number = random.randint(1, 100)
        if new_number >= self.random_number:
            result_message = "Correct"
            winnings = self.bet * 1.5
            updated_points = get_user_data(guild_id, user_id)[0] + winnings
            update_user_points(guild_id, user_id, updated_points)
        else:
            result_message = "Incorrect"
        self.random_number = new_number

        self.embed.set_footer(text=result_message)
        self.embed.set_field_at(0, name="Number", value=f"{new_number}", inline=False)
        await self.message.edit(embed=self.embed, view=self)

    #Lower Button
    @discord.ui.button(label="Lower", style=discord.ButtonStyle.grey)
    async def button_lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        #defer the message
        await interaction.response.defer()

        #check if playable
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        current_points, _ = get_user_data(guild_id, user_id)
        if current_points < self.bet:
            await interaction.followup.send("You do not have enough points to play.", ephemeral=True)
            return


        print("Lower Button Clicked")
        new_number = random.randint(1, 100)
        if new_number <= self.random_number:
            result_message = "Correct"
            winnings = self.bet * 1.5
            updated_points = get_user_data(guild_id, user_id)[0] + winnings
            update_user_points(guild_id, user_id, updated_points)
        else:
            result_message = "Incorrect"
        self.random_number = new_number

        self.embed.set_footer(text=result_message)
        self.embed.set_field_at(0, name="Number", value=f"{new_number}", inline=False)
        await self.message.edit(embed=self.embed, view=self)



    # Button to change bet amount.
    @discord.ui.button(label="Change Bet", style=discord.ButtonStyle.primary)
    async def change_bet_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ChangeBetModal(self)
        await interaction.response.send_modal(modal)

    # Button to show the rules.
    @discord.ui.button(label="Rules", style=discord.ButtonStyle.secondary)
    async def rules_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        rules_text = (
            "**Highlow\n"
            f"- **Cost per Game:** Your current bet (minimum {MIN_BET} points).\n"
            "- **Correct Guess:** You win 1.5x your bet.\n"
            "- **Incorrect Guess:** You lose 1.5x your bet.\n"
        )
        await interaction.response.send_message(rules_text, ephemeral=True)

    # Button to close the game instance.
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()  # Stop listening for interactions
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)
        await interaction.response.send_message("Game Ended.", ephemeral=True)

    # Disable view on timeout.
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass

class highlowCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="highlow", description="Higher or Lower?")
    async def slotmachine(self, interaction: discord.Interaction):
        view = HighLowView(author=interaction.user, bet=DEFAULT_BET)
        embed = view.embed
        # Send the initial message and store it in the view.
        await interaction.response.send_message(embed=embed, view=view)
        print("tried to send an embed")
        view.message = await interaction.original_response()

async def setup(bot: commands.Bot):
    await bot.add_cog(highlowCog(bot))