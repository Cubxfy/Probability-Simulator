import os
import random
import time
import asyncio
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands


# Constants
DEFAULT_BET = 10
MIN_BET = 10
DB_PATH = os.path.join("sqlite", "points.db")
# List of slot emojis. Adjust or add more as needed.

fruit_crate = ["🍒","🍒","🍒","🍒","🍒", "🍋","🍋","🍋", "⭐",]
emoji_crate = ["🥶","🥶","🥶","🥶","🥶", "🔥","🔥","🔥", "🗿",] # for multi crate purposes

CRATE_SYMBOLS = fruit_crate
THE_CRATE = CRATE_SYMBOLS # pop and append to this list

# Winning multipliers for different patterns. You can adjust these values.
WIN_PATTERNS = {
    "CHERRY": 2, # CSGO CASES 
    "LEMON": 5,   # CSGO CASES
    "STAR": 15,     # CSGO CASES
}

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

    def __init__(self, view: "CratesView"):
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
        self.view.embed.description = f"Cost to spin: **{self.view.bet}** points"
        await self.view.message.edit(embed=self.view.embed, view=self.view)
        await interaction.response.send_message(f"Bet updated to **{self.view.bet}** points.", ephemeral=True)

# The main view for the slot machine
class CratesView(discord.ui.View):
    def __init__(self, author: discord.User, bet: int = DEFAULT_BET):
        super().__init__(timeout=120)  # Timeout in seconds
        self.author = author
        self.bet = bet
        self.message = None  # Will store the message after sending.
        # Initial embed showing the slot machine layout (3 empty slots)
        self.embed = discord.Embed(title="Case #1 (others don't exist, I'll make dropdown)", color=discord.Color.blue())
        self.current_symbols = ["🍒", "🍋", "⭐"]
        self.embed.add_field(name="Reels", value=" | ".join(self.current_symbols), inline=False)
        self.embed.description = f"Cost to spin: **{self.bet}** points"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only the original caller may interact.
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This machine isn't for you!", ephemeral=True)
            return False
        return True

    # Button to spin the case.
    @discord.ui.button(label="Spin!", style=discord.ButtonStyle.green)
    async def spin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defer the interaction to avoid the "interaction failed" message.
        await interaction.response.defer()
        button.disabled = True

        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        current_points, _ = get_user_data(guild_id, user_id)
        if current_points < self.bet:
            await interaction.followup.send("You do not have enough points to open this crate.", ephemeral=True)
            return

        # Deduct the bet immediately.
        new_points = current_points - self.bet
        update_user_points(guild_id, user_id, new_points)

        # need to simulate a horizontal thing

        # pop(0), append(random)
        random.shuffle(THE_CRATE)
        
        print("shuffled")
        
        for i in range(2): 
            print("before pop append")
            THE_CRATE.pop(0) # gets rid of first index, andd shifts everything forwards
            THE_CRATE.append(CRATE_SYMBOLS[random.randint(0, len(CRATE_SYMBOLS)-1)])
           
            #everything works up to here

            for s in range(len(THE_CRATE)-1):
                print("attempted print")
                self.embed.set_field_at(0, name="Prize ↓", value=f"{THE_CRATE[s-1]} | {THE_CRATE[s]} | {THE_CRATE[s+1]}", inline=False)
                final_symbol = THE_CRATE[s]
                self.embed.set_footer(text="Spinning!")
                await self.message.edit(embed=self.embed, view=self)
                await asyncio.sleep(0.2)
            
            await self.message.edit(embed=self.embed, view=self)
            await asyncio.sleep(0.1)
        print("done spinning")

        # Determine outcome
        win_multiplier = 0
        result_message = ""

        print("float calc")

        miliseconds = int(time.time() * 1000)
        float = (miliseconds%100) / 100

        # check what symbol
        if final_symbol == "🍒":
            win_multiplier = WIN_PATTERNS["CHERRY"]
            result_message = f"Cherry, float {float}! You win {self.bet * win_multiplier} points!"
        elif final_symbol == "🍋":
            win_multiplier = WIN_PATTERNS["LEMON"]
            result_message = f"Lemon, float {float}! You win {self.bet * win_multiplier} points!"
        elif final_symbol == "⭐":
            win_multiplier = WIN_PATTERNS["STAR"]
            result_message = f"Star, float {float}! You win {self.bet * win_multiplier} points!"
        else:
            win_multiplier = 0
            result_message = f"Nothing Lol, try again?"

        
        
        # If win, update the user's points.
        if win_multiplier > 0:
            winnings = self.bet * win_multiplier + self.bet  # Add back the original bet.
            updated_points = get_user_data(guild_id, user_id)[0] + winnings
            update_user_points(guild_id, user_id, updated_points)
        
        button.disabled = False
        self.embed.set_footer(text=result_message)
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
            "**Case Rules**\n"
            f"- **Cost per Spin:** Your current bet (minimum {MIN_BET} points).\n"
            "this is literally just a crate system."
        )
        await interaction.response.send_message(rules_text, ephemeral=True)

    # Button to close the slot machine.
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()  # Stop listening for interactions
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)
        await interaction.response.send_message("Left the crate store.", ephemeral=True)

    # Disable view on timeout.
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass

class CratesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="crates", description="open a crate!")
    async def crates(self, interaction: discord.Interaction):
        view = CratesView(author=interaction.user, bet=DEFAULT_BET)
        embed = view.embed
        # Send the initial message and store it in the view.
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

async def setup(bot: commands.Bot):
    await bot.add_cog(CratesCog(bot))
