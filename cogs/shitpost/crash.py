import discord
from discord.ext import commands
import random
import sqlite3
import asyncio

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

class Buttons(discord.ui.View):
    def __init__(self, user_id: int, guild_id: int):
        super().__init__()
        self.user_id = user_id
        self.guild_id = guild_id
        self.random_number = random.randint(1, 8)
        self.count = 0
        self.running = True
        
        #DB initialisation
        self.conn = sqlite3.connect("crash.db")
        self.cursor = self.conn.cursor()
        
        #button shit
        self.remove_item(self.button_again)
        self.button_leave_ref = None
        self.button_again_ref = None
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS crash (
                highest_multi INTEGER,
                guild_id INTEGER,
                user_id INTEGER,
                UNIQUE(guild_id, user_id)
            )
        ''')
        self.conn.commit()
        
        self.cursor.execute("SELECT highest_multi FROM crash WHERE user_id = ? AND guild_id = ?", (self.user_id, self.guild_id))
        row = self.cursor.fetchone()
        self.highest = row[0] if row else 0

    #Embed Updater
    async def update_embed(self, interaction: discord.Interaction, result: str):
        if self.count > self.highest and result == "Left":
            self.highest = self.count  

        color = discord.Color.green() if result == "Left" else discord.Color.default()

        if result == "Lose":
            color = discord.Color.red()
        
        embed = discord.Embed(
            title= f"{result}\nScore: {self.count}",
            description=(f"Highest Score: {self.highest}"),
            color=color
        )

        print("Waited on interaction")
               
        if result == "Lose":
            if interaction.response.is_done():
                await interaction.message.edit(embed=embed)
            else:
                await interaction.response.edit_message(embed=embed)
                
        else:
            if interaction.response.is_done():
                await interaction.message.edit(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)

    
    #Start Button
    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.grey)
    async def button_start(self, interaction:discord.Interaction, button: discord.ui.Button):
        print("Start Button Clicked")
        
        self.remove_item(button)        
        self.remove_item(self.button_end)
        self.remove_item(self.button_again)
        
        await interaction.response.edit_message(view=self)
        
        result = "Start"
        
        while self.running:
            print("Crash Game Running")
            new_number = random.randint(1, 8)
            if new_number == self.random_number:
                print("Crash Game Ended")
                result = "Lose"
                await self.update_embed(interaction, result)
                
                if self.button_leave_ref:
                    self.remove_item(self.button_leave_ref)
                if self.button_again_ref:
                    self.add_item(self.button_again_ref)
                
                break
            else:
                self.count += 1
                print("Crash Game + 1")
                result = "InProgress"
                await self.update_embed(interaction, result)
                print("Sleeping")
                await asyncio.sleep(1.2)

    #Leave Button
    @discord.ui.button(label="Cash Out", style=discord.ButtonStyle.grey)
    async def button_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Leave Button Clicked")
        
        self.button_leave_ref = button

        self.running = False
        self.remove_item(button)
        
        await self.update_embed(interaction, "Left")

        self.cursor.execute('''
            INSERT INTO crash (highest_multi, guild_id, user_id)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id) 
            DO UPDATE SET highest_multi = CASE 
                WHEN ? > crash.highest_multi 
                THEN ? 
                ELSE crash.highest_multi 
            END
        ''', (self.highest, self.guild_id, self.user_id))
    
    #Play Again Button
    @discord.ui.button(label="Play Again", style=discord.ButtonStyle.grey)
    async def button_again(self, interaction:discord.Interaction, button: discord.ui.Button):
        print("Again Button Clicked")
        
        self.button_again_ref = button
        
        self.count = 0
        self.running = True
        self.random_number = random.randint(1, 8)
        
        self.clear_items()
        
        self.add_item(self.button_leave)

        while self.running:
            print("Crash Game Running")
            new_number = random.randint(1, 8)
            if new_number == self.random_number:
                print("Crash Game Ended")
                await self.update_embed(interaction, "Lose")
                break
            else:
                self.count += 1
                print("Crash Game +1")
                await self.update_embed(interaction, "InProgress")
                await asyncio.sleep(1.2)
    
        
    #Close Button
    @discord.ui.button(label="Close", style=discord.ButtonStyle.grey)
    async def button_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Close Button Clicked")
        
        self.conn.commit()
        self.conn.close()
        
        embed = discord.Embed(title="**Interaction Ended**", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=None)    

class crashCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("crash.db")
        self.cursor = self.conn.cursor()

    @commands.hybrid_command(aliases=['cr'])
    async def crash(self, ctx):
        view = Buttons(ctx.author.id, ctx.guild.id)
        
        highest_score = view.highest
        
        embed = discord.Embed(title= f"Multiplier: {view.count}", description=f"**Crash**\nGet out before the ship explodes\nHighest Score: {highest_score}", color=discord.Color.green())
        await ctx.send(embed=embed, view=view)

    def cog_unload(self):
        self.conn.close()

async def setup(bot):
    await bot.add_cog(crashCog(bot))