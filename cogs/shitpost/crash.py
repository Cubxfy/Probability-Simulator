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

    def __init__(self, view: "CrashView"):
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
class CrashView(discord.ui.View):
    def __init__(self, author: discord.User, bet: int = DEFAULT_BET):
        super().__init__(timeout=120)  # Timeout in seconds
        self.author = author
        self.bet = bet
        self.message = None  # Will store the message after sending.
        # Initial embed showing the game
        self.embed = discord.Embed(title="Crash", color=discord.Color.blue())
        self.embed.add_field(name="Crash",value=f"🚀 Multiplier: x0", inline=False)
        self.embed.description = f"Cost to play: **{self.bet}** points"

        self.running = True
        self.multi = 0
        self.left = False

        self.random_number = random.randint(1, 50)


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only the original caller may interact.
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green)
    async def button_gamestart(self, interaction: discord.Interaction, button: discord.ui.Button):
        #defer the message
        await interaction.response.defer()

        self.remove_item(self.change_bet_button)
        self.remove_item(self.close_button)
        self.remove_item(self.button_gamestart)

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

        self.left = False

        while self.running:
            print("Crash Game Running")
            new_number = random.randint(1, 50)
            if new_number == self.random_number:
                print("Crash Game Ended")
                result_message = "Lose"
                break
            else:
                self.multi = round(self.multi + 0.1, 1) #rounding!
                print("Crash Game + 1")
                result_message = "InProgress"   
                print("Sleeping")
                await asyncio.sleep(1)
            
            self.embed.set_footer(text=result_message)
            self.embed.set_field_at(0, name="Multiplier", value=f"🚀 {self.multi}", inline=False)
            await self.message.edit(embed=self.embed, view=self)

        if not self.left:
            self.embed.set_footer(text = result_message)
            self.embed.set_field_at(0, name="Game Ended", value=f"💥 {self.multi}")
            await self.message.edit(embed=self.embed, view=self)        
        
        self.add_item(self.change_bet_button)
        self.add_item(self.close_button)
        self.add_item(self.button_gamestart)

    #Leave Button
    @discord.ui.button(label="Cash Out", style=discord.ButtonStyle.grey)
    async def button_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        #defer the message
        await interaction.response.defer()

        self.left = True
        
        print("Leave Button Clicked")

        self.running = False
        winnings = self.bet * self.multi
        updated_points = get_user_data(guild_id, user_id)[0] + winnings
        update_user_points(guild_id, user_id, updated_points)
        
        result_message = "Left"

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
            "**Crash\n"
            f"- **Cost per Game:** Your current bet (minimum {MIN_BET} points).\n"
            "- **How it works** Bet on a curving multiplier, get out before the multiplier drops to 0.\n"
        )
        await interaction.response.send_message(rules_text, ephemeral=True)

    # Button to close the game instance.
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.running = False
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

class crashCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="crash", description="get out before the rocket explodes")
    async def slotmachine(self, interaction: discord.Interaction):
        view = CrashView(author=interaction.user, bet=DEFAULT_BET)
        embed = view.embed
        # Send the initial message and store it in the view.
        await interaction.response.send_message(embed=embed, view=view)
        print("tried to send an embed")
        view.message = await interaction.original_response()

async def setup(bot: commands.Bot):
    await bot.add_cog(crashCog(bot))    