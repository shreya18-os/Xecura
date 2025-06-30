import discord
from discord.ext import commands
import json
from typing import Optional
from discord.ui import Select, View
import os

# Initialize bot configuration
DEFAULT_PREFIX = 'x!'
OWNER_ID = 1101467683083530331

# Load bot token from environment variable (Railway secrets)
TOKEN = os.getenv('BOT_TOKEN')

# Initialize data storage
class DataManager:
    def __init__(self):
        self.badges = {}
        self.no_prefix_users = set()
        self.load_data()
    
    def load_data(self):
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
                self.badges = data.get('badges', {})
                self.no_prefix_users = set(data.get('no_prefix_users', []))
        except FileNotFoundError:
            self.save_data()
    
    def save_data(self):
        with open('data.json', 'w') as f:
            json.dump({
                'badges': self.badges,
                'no_prefix_users': list(self.no_prefix_users)
            }, f, indent=4)

data_manager = DataManager()

# Custom prefix handler
def get_prefix(bot, message):
    if str(message.author.id) in data_manager.no_prefix_users:
        return commands.when_mentioned_or('')(bot, message)
    return commands.when_mentioned_or(DEFAULT_PREFIX)(bot, message)

bot = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all(), help_command=None)

# Badge definitions
BADGES = {
    'owner': '👑',
    'admin': '🛡️',
    'staff': '🔧',
    'no_prefix': '🎯',
    'no_badge': '❌'
}

# Help command with dropdown
class HelpDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label='General',
                description='General commands',
                emoji='⚙️'
            ),
            discord.SelectOption(
                label='Profile',
                description='Profile related commands',
                emoji='👤'
            ),
            discord.SelectOption(
                label='Admin',
                description='Administrative commands',
                emoji='🛠️'
            )
        ]
        super().__init__(placeholder='Select a category', options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        if category == 'General':
            commands_list = "```\nhelp - Show this help menu\nping - Check bot's latency\n```"
        elif category == 'Profile':
            commands_list = "```\nprofile - View your or someone else's profile\n```"
        elif category == 'Admin':
            commands_list = "```\ngivebadge - Give a badge to a user (Owner only)\nremovebadge - Remove a badge from a user (Owner only)\ntogglenoprefix - Toggle no-prefix mode for a user (Owner only)\n```"

        embed = discord.Embed(
            title=f'{category} Commands',
            description=commands_list,
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed)

class HelpView(View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpDropdown())

@bot.event
async def on_ready():
    print(f'{bot.user} is ready!')
    await bot.change_presence(activity=discord.Game(name=f"{DEFAULT_PREFIX}help"))

import traceback
@bot.event
async def on_command_error(ctx, error):
    traceback.print_exception(type(error), error, error.__traceback__)
    if isinstance(error, commands.CommandNotFound):
        if str(ctx.author.id) not in data_manager.no_prefix_users:
            embed = discord.Embed(
                title='❌ Error',
                description='Command not found!',
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

@bot.command(name='help')
async def custom_help(ctx):
    embed = discord.Embed(
        title='📖 Help Menu',
        description='Select a category below to view commands',
        color=discord.Color.blue()
    )
    view = HelpView()
    await ctx.send(embed=embed, view=view)

@bot.command(name='profile')
async def profile(ctx, user: Optional[discord.Member] = None):
    user = user or ctx.author
    user_badges = data_manager.badges.get(str(user.id), [])
    badge_display = ' '.join(BADGES[badge] for badge in user_badges) or BADGES['no_badge']
    
    embed = discord.Embed(
        title=f'👤 {user.name}\'s Profile',
        color=discord.Color.blue()
    )
    embed.add_field(name='User ID', value=user.id)
    embed.add_field(name='Badges', value=badge_display)
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    
    await ctx.send(embed=embed)

@bot.command(name='givebadge')
async def give_badge(ctx, user: discord.Member, badge: str):
    if ctx.author.id != OWNER_ID:
        return await ctx.send('❌ Only the bot owner can use this command!')
    
    if badge not in BADGES or badge == 'no_badge':
        return await ctx.send('❌ Invalid badge!')
    
    user_id = str(user.id)
    if user_id not in data_manager.badges:
        data_manager.badges[user_id] = []
    
    if badge not in data_manager.badges[user_id]:
        data_manager.badges[user_id].append(badge)
        data_manager.save_data()
        await ctx.send(f'✅ Added {BADGES[badge]} to {user.mention}')
    else:
        await ctx.send(f'❌ {user.mention} already has this badge!')

@bot.command(name='removebadge')
async def remove_badge(ctx, user: discord.Member, badge: str):
    if ctx.author.id != OWNER_ID:
        return await ctx.send('❌ Only the bot owner can use this command!')
    
    user_id = str(user.id)
    if user_id in data_manager.badges and badge in data_manager.badges[user_id]:
        data_manager.badges[user_id].remove(badge)
        data_manager.save_data()
        await ctx.send(f'✅ Removed {BADGES[badge]} from {user.mention}')
    else:
        await ctx.send(f'❌ {user.mention} doesn\'t have this badge!')

@bot.command(name='togglenoprefix')
async def toggle_no_prefix(ctx, user: discord.Member):
    if ctx.author.id != OWNER_ID:
        return await ctx.send('❌ Only the bot owner can use this command!')
    
    user_id = str(user.id)
    if user_id in data_manager.no_prefix_users:
        data_manager.no_prefix_users.remove(user_id)
        await ctx.send(f'✅ Disabled no-prefix mode for {user.mention}')
    else:
        data_manager.no_prefix_users.add(user_id)
        await ctx.send(f'✅ Enabled no-prefix mode for {user.mention}')
    data_manager.save_data()

@bot.command(name='ping')
async def ping(ctx):
    embed = discord.Embed(
        title='🏓 Pong!',
        description=f'Latency: {round(bot.latency * 1000)}ms',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# Run the bot
bot.run(TOKEN)
