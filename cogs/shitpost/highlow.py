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
    
    async def update_embed(self, interaction: discord.Interaction, result: str):
        """ Updates the embed with the new result and sends an edited message. """
        if self.count > self.highest:
            self.highest = self.count  # Update highest score if beaten

        embed = discord.Embed(
            title="Highlow Game",
            description=(
                f"**{result}**\n"
                f"Current Streak: {self.count}\n"
                f"New Number: {self.random_number}\n"
                f"Highest Score: {self.highest}"
            ),
            color=discord.Color.blue()
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
        await interaction.response.edit_message(content="**Game ended.**", view=None)

class highlowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["hl"])
    async def highlow(self, ctx):
        view = Buttons()
        embed = discord.Embed(title= "Highlow Game", description = f"Starting number: {view.random_number}\nHighest Score: {view.highest}", color=000000)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(highlowCog(bot))