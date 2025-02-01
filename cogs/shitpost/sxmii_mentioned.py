import discord
from discord.ext import commands

class SxmiiMention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.images = {
            "sxmii": "https://cdn.discordapp.com/attachments/1333286052458266755/1333894783177064499/Work_of_art.jpg?ex=679a8dd2&is=67993c52&hm=a0984f65d2bfa8b9893f4be2e51ec880dec22ba0f4be1135c0a35aa8af549b3e&"
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        for phrase, image_url in self.images.items():
            if phrase in message.content.lower():
                await message.channel.send(image_url)
                break

async def setup(bot):
    await bot.add_cog(SxmiiMention(bot))