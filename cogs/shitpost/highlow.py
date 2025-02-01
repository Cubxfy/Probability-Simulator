import discord
from discord.ext import commands
import random

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

class Buttons(discord.ui.View):
    def __init__(self, author:discord.User):
        super().__init__()
        self.owner = author
        self.random_number = random.randint(1, 100)
        self.count = 0
        self.highest = 0
    
    async def update_embed(self, interaction: discord.Interaction, result: str):
        if self.count > self.highest:
            self.highest = self.count  

        if result == "Correct":
            embed = discord.Embed(
                title= f"{result}\nNew Number: {self.random_number}",
                description=(f"Current Streak: {self.count}\nHighest Score: {self.highest}"),
                color=discord.Color.green()
            )
        
        if result == "Incorrect":
            embed = discord.Embed(
                title= f"{result}\nNew Number: {self.random_number}",
                description=(f"Current Streak: {self.count}\nHighest Score: {self.highest}"),
                color=discord.Color.red()
            )

        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Higher", style=discord.ButtonStyle.grey)
    async def button_higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Higher Button Clicked")
        new_number = random.randint(1, 100)
        if new_number > self.random_number:
            result = "Correct"
            self.count += 1
        else:
            result = "Incorrect"
            if self.count >= self.highest:
                self.count == self.highest
            self.count = 0
        self.random_number = new_number
        await self.update_embed(interaction, result)

    @discord.ui.button(label="Lower", style=discord.ButtonStyle.grey)
    async def button_lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Lower Button Clicked")
        new_number = random.randint(1, 100)
        if new_number < self.random_number:
            result = "Correct"
            self.count += 1
        else:
            result = "Incorrect"
            if self.count >= self.highest:
                self.count == self.highest 
            self.count = 0
        self.random_number = new_number
        await self.update_embed(interaction, result)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.grey)
    async def button_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Close Button Clicked")
        embed = discord.Embed(title="**Game Ended**", description=f"Highest Score: {self.highest}", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=None)


class highlowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["hl"])
    async def highlow(self, ctx):
        view = Buttons()
        embed = discord.Embed(title= f"Starting number: {view.random_number}", description="**HighLow Game**\nPredict whether the next number will be higher or lower", color=discord.Color.green())
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(highlowCog(bot))