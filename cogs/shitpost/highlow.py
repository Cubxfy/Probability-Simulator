import discord
from discord.ext import commands
import random

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

class Buttons(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.random_number = random.randint(1, 100)
        self.count = 0
        self.highest = 0

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
        await interaction.response.edit_message(
            content=f"{result}\nCurrent Streak: {self.count}\nNew number: {self.random_number}",
            view=self
        )

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
        await interaction.response.edit_message(
            content=f"{result}\nCurrent Streak: {self.count}\nNew number: {self.random_number}",
            view=self
        )

    @discord.ui.button(label="Close", style=discord.ButtonStyle.grey)
    async def button_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Close Button Clicked")
        await interaction.response.edit_message(content="**Game ended.**", view=None)

class highlowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["hl"])
    async def highlow(self, ctx):
        view = Buttons()
        embed = discord.Embed(title= "Test", url = "Test", description = "embed content", color=000000)
        await ctx.send(embed=f"Starting number: {view.random_number}\nHighest Score: {view.highest}", view=view)

async def setup(bot):
    await bot.add_cog(highlowCog(bot))