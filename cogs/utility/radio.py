import discord
from discord.ext import commands
import sqlite3
import asyncio
from difflib import get_close_matches
from datetime import datetime
import re

class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('radio_library.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_library (
                guild_id INTEGER,
                user_id INTEGER,
                stream_name TEXT,
                stream_url TEXT,
                PRIMARY KEY (guild_id, user_id, stream_name)
            )
        ''')
        self.conn.commit()

    def cog_unload(self):
        self.conn.close()

    @commands.hybrid_command(
        name='addstream',
        description='Add a radio stream to your personal library.'
    )
    @discord.app_commands.describe(
        name='The name of the stream',
        url='The URL of the radio stream'
    )
    async def add_stream(self, ctx, name: str, url: str):
        guild_id = ctx.guild.id
        user_id = ctx.author.id

        try:
            self.cursor.execute('''
                INSERT INTO user_library (guild_id, user_id, stream_name, stream_url)
                VALUES (?, ?, ?, ?)
            ''', (guild_id, user_id, name, url))
            self.conn.commit()
            await ctx.send(f"Stream '{name}' added to your library.")
        except sqlite3.IntegrityError:
            await ctx.send(f"A stream with the name '{name}' already exists in your library.")

    @commands.hybrid_command(
        name='removestream',
        description='Remove a radio stream from your personal library.'
    )
    @discord.app_commands.describe(
        name='The name of the stream to remove'
    )
    async def remove_stream(self, ctx, name: str):
        guild_id = ctx.guild.id
        user_id = ctx.author.id

        self.cursor.execute('''
            DELETE FROM user_library WHERE guild_id = ? AND user_id = ? AND stream_name = ?
        ''', (guild_id, user_id, name))
        self.conn.commit()

        if self.cursor.rowcount > 0:
            await ctx.send(f"Stream '{name}' removed from your library.")
        else:
            await ctx.send(f"No stream found with the name '{name}' in your library.")

    @commands.hybrid_command(
        name='playstream',
        description='Play a radio stream from a link or your personal library.'
    )
    @discord.app_commands.describe(
        source='Specify "link" to play from a URL or "library" to play from your saved streams',
        name='The name of the stream or the URL to play'
    )
    async def play_stream(self, ctx, source: str, name: str):
        if not ctx.author.voice:
            await ctx.send("You are not connected to a voice channel.")
            return

        guild_id = ctx.guild.id
        user_id = ctx.author.id

        if source.lower() == "link":
            url = name
            # Check if the URL is a YouTube link
            if re.match(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/', url):
                await ctx.send("YouTube videos are unsupported. Please provide a direct link to an MP3, MP4, or other direct audio file.")
                return
        elif source.lower() == "library":
            self.cursor.execute('''
                SELECT stream_name, stream_url FROM user_library WHERE guild_id = ? AND user_id = ?
            ''', (guild_id, user_id))
            results = self.cursor.fetchall()

            if not results:
                await ctx.send("Your library is empty.")
                return

            stream_names = [stream_name for stream_name, _ in results]
            matches = get_close_matches(name, stream_names, n=2, cutoff=0.4)

            if len(matches) == 0:
                await ctx.send(f"No close matches found for '{name}' in your library.")
                return
            elif len(matches) > 1:
                await ctx.send(f"Multiple matches found for '{name}': {', '.join(matches)}. Please be more specific.")
                return
            else:
                # Get the URL of the closest match
                match_name = matches[0]
                url = next(url for stream_name, url in results if stream_name == match_name)
        else:
            await ctx.send("Invalid source. Please specify 'link' or 'library'.")
            return

        # Check if the bot is already connected to a voice channel
        voice_client = ctx.voice_client
        if voice_client is None:
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()

        ffmpeg_options = {
            'options': '-vn'
        }
        audio_source = discord.FFmpegPCMAudio(url, **ffmpeg_options)

        if voice_client.is_playing():
            voice_client.stop()  # Stop the current audio before playing the new one

        voice_client.play(audio_source, after=lambda e: print(f"Finished playing: {e}"))
        await ctx.send(f"Now playing: {name}")

    @commands.hybrid_command(
        name='stopstream',
        description='Stop the current radio stream and disconnect from the voice channel.'
    )
    async def stop_stream(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Stopped playing and disconnected from the voice channel.")
        else:
            await ctx.send("The bot is not connected to a voice channel.")

    @commands.hybrid_command(
        name='liststreams',
        description='List all radio streams in your personal library.'
    )
    async def list_streams(self, ctx):
        guild_id = ctx.guild.id
        user_id = ctx.author.id

        self.cursor.execute('''
            SELECT stream_name, stream_url FROM user_library WHERE guild_id = ? AND user_id = ?
        ''', (guild_id, user_id))
        results = self.cursor.fetchall()

        if results:
            embed = discord.Embed(colour=0x8080c0, timestamp=datetime.now())
            embed.set_author(name=f"{ctx.author.display_name} - Stream Library")

            for stream_name, stream_url in results:
                embed.add_field(name=stream_name, value=stream_url, inline=False)

            embed.set_footer(text="Gooberbot", icon_url="https://slate.dan.onl/slate.png")
            await ctx.send(embed=embed)
        else:
            await ctx.send("Your library is empty.")

async def setup(bot):
    await bot.add_cog(Radio(bot))