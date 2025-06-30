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
                # Convert lists to sets for badges
                self.badges = {user_id: set(badges) for user_id, badges in data.get('badges', {}).items()}
                self.no_prefix_users = set(data.get('no_prefix_users', []))
        except FileNotFoundError:
            self.save_data()
    
    def save_data(self):
        with open('data.json', 'w') as f:
            # Convert sets back to lists for JSON serialization
            json_data = {
                'badges': {user_id: list(badges) for user_id, badges in self.badges.items()},
                'no_prefix_users': list(self.no_prefix_users)
            }
            json.dump(json_data, f, indent=4)

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
    def __init__(self, ctx):
        self.ctx = ctx
        options = [
            discord.SelectOption(label='General', description='General commands', emoji='⚙️'),
            discord.SelectOption(label='Profile', description='Profile-related commands', emoji='👤'),
            discord.SelectOption(label='Admin', description='Administrative commands', emoji='🛠️')
        ]
        super().__init__(placeholder='Select a category', options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ You can't use this menu.", ephemeral=True)

        category = self.values[0]
        embed = discord.Embed(
            title=f'{category} Commands',
            color=discord.Color.blue()
        )

        if category == 'General':
            cmds = ['help', 'ping']
        elif category == 'Profile':
            cmds = ['profile']
        elif category == 'Admin':
            cmds = ['givebadge', 'removebadge', 'togglenoprefix']
        else:
            cmds = []

        for command in bot.commands:
            if command.name in cmds:
                embed.add_field(
                    name=f"`{command.name}`",
                    value=command.help or "No description.",
                    inline=False
                )

        await interaction.response.edit_message(embed=embed)

class HelpView(View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.add_item(HelpDropdown(ctx))

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

@bot.command(name='help', help="Show the help menu with categorized commands.")
async def custom_help(ctx):
    embed = discord.Embed(
        title='📖 Help Menu',
        description='Please select a category below to view commands.',
        color=discord.Color.blue()
    )
    view = HelpView(ctx)
    await ctx.send(embed=embed, view=view)


@bot.command(name='profile')
async def profile(ctx, member: Optional[discord.Member] = None):
    member = member or ctx.author
    
    embed = discord.Embed(
        title=f'Profile - {member}',
        color=member.color
    )
    
    # Add user info
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    embed.add_field(name='<:idi1:1389183049916481646> User ID', value=member.id, inline=True)
    embed.add_field(name='📅 Joined', value=member.joined_at.strftime('%Y-%m-%d'), inline=True)
    
    # Add badges
    badges = data_manager.badges.get(str(member.id), set())
    badge_display = '\n'.join([BADGES[badge] for badge in badges]) if badges else BADGES['no_badge']
    badge_display = badge_display.replace('👑', '<:owner1:1389180694814654474>')\
                               .replace('🛡️', '<a:staff112:1389180853195771906>')\
                               .replace('⚡', '<:admin1:1389181036755161221>')\
                               .replace('❌', '<a:nope1:1389178762020520109>')
    embed.add_field(
        name='<a:badge1:1389182687947919370> Badges',
        value=badge_display,
        inline=False
    )
    
    # Add no-prefix status
    no_prefix_status = '<:tick1:1389181551358509077> Enabled' if str(member.id) in data_manager.no_prefix_users else '<a:nope1:1389178762020520109> Disabled'
    embed.add_field(name='<:prefix1:1389181942553116695> No-Prefix Status', value=no_prefix_status, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='givebadge')
async def give_badge(ctx, user: discord.Member, badge: str):
    if ctx.author.id != OWNER_ID:
        return await ctx.send('<error:ID> Only the bot owner can use this command!')
    
    if badge not in BADGES or badge == 'no_badge':
        return await ctx.send('<error:ID> Invalid badge!')
    
    user_id = str(user.id)
    if user_id not in data_manager.badges:
        data_manager.badges[user_id] = set()
    
    if badge not in data_manager.badges[user_id]:
        data_manager.badges[user_id].add(badge)
        data_manager.save_data()
        await ctx.send(f'<success:ID> Added {BADGES[badge]} to {user.mention}')
    else:
        await ctx.send(f'<error:ID> {user.mention} already has this badge!')

@bot.command(name='removebadge')
async def remove_badge(ctx, user: discord.Member, badge: str):
    if ctx.author.id != OWNER_ID:
        return await ctx.send('<error:ID> Only the bot owner can use this command!')
    
    user_id = str(user.id)
    if user_id in data_manager.badges and badge in data_manager.badges[user_id]:
        data_manager.badges[user_id].remove(badge)
        if not data_manager.badges[user_id]:  # Remove empty set
            del data_manager.badges[user_id]
        data_manager.save_data()
        await ctx.send(f'<success:ID> Removed {BADGES[badge]} from {user.mention}')
    else:
        await ctx.send(f'<error:ID> {user.mention} doesn\'t have this badge!')

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
