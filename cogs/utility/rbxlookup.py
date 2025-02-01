import discord
from discord.ext import commands
import aiohttp

class RobloxProfile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="robloxprofile",
        description="Fetches a Roblox user's profile information."
    )
    async def robloxprofile(self, ctx: commands.Context, username: str):
        # Base API URLs
        user_search_api = f"https://users.roblox.com/v1/users/search?keyword={username}&limit=10"
        user_info_api = "https://users.roblox.com/v1/users/{user_id}"
        friends_count_api = "https://friends.roblox.com/v1/users/{user_id}/friends/count"
        groups_api = "https://groups.roblox.com/v1/users/{user_id}/groups/roles"
        avatar_api = "https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=true"

        async with aiohttp.ClientSession() as session:
            try:
                # Fetch users based on the username keyword
                async with session.get(user_search_api) as user_response:
                    if user_response.status != 200:
                        await ctx.send(f"Failed to fetch user info. HTTP Status: {user_response.status}")
                        return
                    user_data = await user_response.json()
                    if not user_data.get('data'):
                        await ctx.send(f"User '{username}' not found.")
                        return

                    # Find the exact username match
                    user = next((u for u in user_data['data'] if u['name'].lower() == username.lower()), None)
                    if not user:
                        await ctx.send(f"User '{username}' not found.")
                        return

                    user_id = user['id']
                    display_name = user.get('displayName', username)

                # Fetch user's detailed information to get the description
                async with session.get(user_info_api.format(user_id=user_id)) as info_response:
                    if info_response.status != 200:
                        description = "Unable to fetch bio."
                    else:
                        info_data = await info_response.json()
                        description = info_data.get('description', 'No bio available.')

                # Fetch user's avatar headshot
                async with session.get(avatar_api.format(user_id=user_id)) as avatar_response:
                    avatar_url = None
                    if avatar_response.status == 200:
                        avatar_data = await avatar_response.json()
                        if avatar_data.get('data'):
                            avatar_url = avatar_data['data'][0].get('imageUrl')

                # Fetch user's friend count
                async with session.get(friends_count_api.format(user_id=user_id)) as friends_response:
                    if friends_response.status != 200:
                        friend_count = "Unable to fetch friend count."
                    else:
                        friends_data = await friends_response.json()
                        friend_count = friends_data.get('count', 'Unknown')

                # Fetch user's groups and count them
                async with session.get(groups_api.format(user_id=user_id)) as groups_response:
                    if groups_response.status != 200:
                        group_count = "Unable to fetch groups."
                    else:
                        groups_data = await groups_response.json()
                        group_count = len(groups_data.get('data', []))

                # Create an embed for the profile information
                embed = discord.Embed(
                    title=f"Roblox Profile: {display_name}",
                    color=discord.Color.blue()
                )
                if avatar_url:
                    embed.set_thumbnail(url=avatar_url)
                embed.add_field(name="Username", value=username, inline=False)
                embed.add_field(name="Display Name", value=display_name, inline=False)
                embed.add_field(name="Bio", value=description or "No bio available.", inline=False)
                embed.add_field(name="Total Friends", value=friend_count, inline=False)
                embed.add_field(name="Total Groups", value=group_count, inline=False)

                await ctx.send(embed=embed)

            except Exception as e:
                await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(RobloxProfile(bot))
