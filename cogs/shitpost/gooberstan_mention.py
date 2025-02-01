import discord
from discord.ext import commands
import random

class GooberstanMention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.images = [
            "https://cdn.discordapp.com/attachments/1333286052458266755/1333890719936675940/image.jpg?ex=679a8a0a&is=6799388a&hm=bd27abe1c04c1c659742202655d9d55bd78c3659ead4c1b43579bc652c0694be&",
            "https://cdn.discordapp.com/attachments/1333286052458266755/1333890871845978153/image.jpg?ex=679a8a2e&is=679938ae&hm=72ec668a22d1b21dd18d3f57e11fa3b08a5a6792759d84989eac611d22e3e392&",
            "https://media.discordapp.net/attachments/1333286052458266755/1333554483510251580/20250127_224903.jpg?ex=6799f9a5&is=6798a825&hm=087c7aee8801ec60e39005db00274a59ebf579722dd434e160ccb0913bd80a33&=&format=webp&width=958&height=206",
            "https://cdn.discordapp.com/attachments/1333293671101104141/1333893080889299028/image.png?ex=679a8c3d&is=67993abd&hm=a71f9d5fc9c943abeb208bdf06f4af3a61d429d8e37d2c46b0ad7fb7ba62abf8&" 
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if 'gooberstan' in message.content.lower():
            random_image = random.choice(self.images)
            await message.channel.send(random_image)

async def setup(bot):
    await bot.add_cog(GooberstanMention(bot))