import discord
from discord.ext import commands
import psutil
import time
from datetime import timedelta

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.hybrid_command(
        name="status",
        description="Get the bot's hardware specifications and uptime."
    )
    async def status(self, ctx: commands.Context):
        # Get system information
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        total_memory = memory_info.total // (1024 ** 2)  # Convert bytes to MB
        used_memory = memory_info.used // (1024 ** 2)  # Convert bytes to MB
        num_cpus = psutil.cpu_count(logical=True)
        num_physical_cpus = psutil.cpu_count(logical=False)

        # Calculate uptime
        current_time = time.time()
        uptime_seconds = int(current_time - self.start_time)
        uptime_str = str(timedelta(seconds=uptime_seconds))

        # Create an embed message
        embed = discord.Embed(
            title="Bot Status",
            color=discord.Color.green()
        )
        embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="Memory Usage", value=f"{used_memory}MB / {total_memory}MB", inline=True)
        embed.add_field(name="Total RAM", value=f"{total_memory}MB", inline=True)
        embed.add_field(name="Logical CPUs", value=f"{num_cpus}", inline=True)
        embed.add_field(name="Physical CPUs", value=f"{num_physical_cpus}", inline=True)
        embed.add_field(name="Uptime", value=uptime_str, inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Status(bot))