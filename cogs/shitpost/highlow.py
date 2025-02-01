import discord
from discord.ext import commands
import random
import sqlite3

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

class Buttons(discord.ui.View):
    def __init__(self, user_id: int, guild_id: int):
        super().__init__()
        self.user_id = user_id
        self.guild_id = guild_id
        self.random_number = random.randint(1, 100)
        self.count = 0      
        
        #DB initialisation
        self.conn = sqlite3.connect("gambling.db")
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS highlow (
                highest_streak INTEGER,
                guild_id INTEGER,
                user_id INTEGER UNIQUE
            )
        ''')
        self.conn.commit()
        
        self.cursor.execute("SELECT highest_streak FROM highlow WHERE user_id = ? AND guild_id = ?", (self.user_id, self.guild_id))
        row = self.cursor.fetchone()
        self.highest = row[0] if row else 0

    #Embed Updater
    async def update_embed(self, interaction: discord.Interaction, result: str):
        if self.count > self.highest:
            self.highest = self.count  

        color = discord.Color.green() if result == "Correct" else discord.Color.red()   

        embed = discord.Embed(
            title= f"{result}\nNew Number: {self.random_number}",
            description=(f"Current Score: {self.count}\nHighest Score: {self.highest}"),
            color=color
        )

        await interaction.response.edit_message(embed=embed, view=self)
    
    #Higher Button
    @discord.ui.button(label="Higher", style=discord.ButtonStyle.grey)
    async def button_higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Higher Button Clicked")
        new_number = random.randint(1, 100)
        if new_number >= self.random_number:
            result = "Correct"
            self.count += 1
        else:
            result = "Incorrect"
            if self.count > self.highest:
                self.highest = self.count
            self.count = 0
        self.random_number = new_number
        await self.update_embed(interaction, result)

    #Lower Button
    @discord.ui.button(label="Lower", style=discord.ButtonStyle.grey)
    async def button_lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Lower Button Clicked")
        new_number = random.randint(1, 100)
        if new_number <= self.random_number:
            result = "Correct"
            self.count += 1
        else:
            result = "Incorrect"
            if self.count >= self.highest:
                self.highest = self.count 
            self.count = 0
        self.random_number = new_number
        await self.update_embed(interaction, result)

    #Close Button
    @discord.ui.button(label="Close", style=discord.ButtonStyle.grey)
    async def button_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Close Button Clicked")
        
        self.cursor.execute(
            "INSERT INTO highlow (highest_streak, guild_id, user_id) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET highest_streak = MAX(highest_streak, excluded.highest_streak)",
            (self.highest, self.guild_id, self.user_id)
        )
        
        self.conn.commit()
        self.conn.close()
        
        embed = discord.Embed(title="**Game Ended**", description=f"Highest Score: {self.highest}", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=None)


class highlowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("gambling.db")
        self.cursor = self.conn.cursor()

    @commands.hybrid_command(aliases=["hl"])
    async def highlow(self, ctx):
        view = Buttons(ctx.author.id, ctx.guild.id)
        
        highest_score = view.highest
        
        embed = discord.Embed(title= f"Starting number: {view.random_number}", description=f"**HighLow**\nPredict whether the next number will be higher or lower\nHighest Score: {highest_score}", color=discord.Color.green())
        await ctx.send(embed=embed, view=view)

    def cog_unload(self):
        self.conn.close()

async def setup(bot):
    await bot.add_cog(highlowCog(bot))