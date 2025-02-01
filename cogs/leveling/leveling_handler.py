import discord
from discord.ext import commands, tasks
import sqlite3
import asyncio
import math
import random
from datetime import datetime, timedelta

class LevelingHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('levels.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS levels (
                guild_id INTEGER,
                user_id INTEGER,
                xp INTEGER NOT NULL,
                level INTEGER NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        self.conn.commit()

        self.xp_per_message = 20  # Increased XP per message
        self.xp_decay = 0.05  # Reduced decay for higher XP gain

    def cog_unload(self):
        self.conn.close()

    def calculate_required_xp(self, level):
        return 100 * (level ** 2)

    async def award_xp(self, guild_id, user_id):
        if random.random() > self.xp_decay:
            return

        self.cursor.execute('SELECT xp, level FROM levels WHERE guild_id = ? AND user_id = ?', (guild_id, user_id))
        result = self.cursor.fetchone()

        if result:
            xp, level = result
            xp += self.xp_per_message
        else:
            xp = self.xp_per_message
            level = 1

        required_xp = self.calculate_required_xp(level + 1)
        leveled_up = False
        if xp >= required_xp:
            level += 1
            leveled_up = True

        self.cursor.execute('''
            INSERT INTO levels (guild_id, user_id, xp, level) VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET xp=excluded.xp, level=excluded.level
        ''', (guild_id, user_id, xp, level))
        self.conn.commit()

        return leveled_up, level

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        guild_id = message.guild.id
        user_id = message.author.id

        result = await self.award_xp(guild_id, user_id)
        if result is None:
            return
        leveled_up, level = result

        if leveled_up:
            channel = message.channel
            await channel.send(f"🎉 Congratulations {message.author.mention}! You've reached level {level}!")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"LevelingHandler cog loaded. Logged in as {self.bot.user}.")

async def setup(bot):
    await bot.add_cog(LevelingHandler(bot))