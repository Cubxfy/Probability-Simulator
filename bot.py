import os
import discord
from discord.ext import commands
from config import DISCORD_TOKEN, DISABLED_COMMANDS
import asyncio

# Initialize bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True  # Required for user data
intents.message_content = True  # Required to read message content

# Use os.getenv for command prefix with a default value
command_prefix = os.getenv("COMMAND_PREFIX", "!")

bot = commands.Bot(command_prefix=command_prefix, intents=intents)

async def load_cogs():
    for folder in os.listdir("cogs"):
        folder_path = os.path.join("cogs", folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith(".py") and file[:-3] not in DISABLED_COMMANDS.get(folder, []):
                    extension = f"cogs.{folder}.{file[:-3]}"
                    try:
                        await bot.load_extension(extension)
                        print(f"Loaded extension: {extension}")
                    except Exception as e:
                        print(f"Failed to load extension {extension}: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    try:
        synced = await bot.tree.sync()  # Sync all slash commands globally
        print(f"Synced {len(synced)} commands globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

async def main():
    await load_cogs()
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    if DISCORD_TOKEN is None:
        raise ValueError("DISCORD_TOKEN is not set. Please check your .env file.")
    asyncio.run(main())
