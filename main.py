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
    def __init__(self):
        options = [
            discord.SelectOption(
                label='General',
                description='Basic utility commands',
                emoji='<:general1:1389183049916481646>'
            ),
            discord.SelectOption(
                label='Profile',
                description='User profile and badge management',
                emoji='<:profile1:1389182687947919370>'
            ),
            discord.SelectOption(
                label='Moderation',
                description='Server management commands',
                emoji='<:mod1:1389181036755161221>'
            ),
            discord.SelectOption(
                label='Admin',
                description='Administrative commands',
                emoji='<:admin1:1389181036755161221>'
            )
        ]
        super().__init__(placeholder='✨ Select a category', options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name=f'{category} Commands', icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        if category == 'General':
            embed.description = "Here are the general utility commands:"
            embed.add_field(
                name='<:help1:1389181551358509077> `help`',
                value='Show this help menu',
                inline=False
            )
            embed.add_field(
                name='<:ping1:1389181942553116695> `ping`',
                value='Check bot\'s latency',
                inline=False
            )
        
        elif category == 'Profile':
            embed.description = "Manage your profile and badges:"
            embed.add_field(
                name='<:profile1:1389182687947919370> `profile [user]`',
                value='View your or someone else\'s profile',
                inline=False
            )
        
        elif category == 'Moderation':
            embed.description = "Server moderation commands:"
            embed.add_field(
                name='<:kick1:1389178762020520109> `kick <user> [reason]`',
                value='Kick a member from the server',
                inline=False
            )
            embed.add_field(
                name='<:ban1:1389180694814654474> `ban <user> [reason]`',
                value='Ban a member from the server',
                inline=False
            )
            embed.add_field(
                name='<:unban1:1389180853195771906> `unban <user_id>`',
                value='Unban a user from the server',
                inline=False
            )
            embed.add_field(
                name='<:clear1:1389181036755161221> `clear <amount>`',
                value='Delete a specified number of messages',
                inline=False
            )
            embed.add_field(
                name='<:warn1:1389181551358509077> `warn <user> [reason]`',
                value='Warn a member',
                inline=False
            )
        
        elif category == 'Admin':
            embed.description = "Owner-only administrative commands:"
            embed.add_field(
                name='<:badge1:1389182687947919370> `givebadge <user> <badge>`',
                value='Give a badge to a user',
                inline=False
            )
            embed.add_field(
                name='<:nobadge1:1389178762020520109> `removebadge <user> <badge>`',
                value='Remove a badge from a user',
                inline=False
            )
            embed.add_field(
                name='<:prefix1:1389181942553116695> `togglenoprefix <user>`',
                value='Toggle no-prefix mode for a user',
                inline=False
            )
        
        embed.set_footer(text=f'Prefix: {DEFAULT_PREFIX} | Total Commands: {len(bot.commands)}')
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
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='You do not have permission to use this command!',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description=f'Missing required argument: {error.param.name}',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        if str(ctx.author.id) not in data_manager.no_prefix_users:
            embed = discord.Embed(
                title='<a:nope1:1389178762020520109> Error',
                description='Command not found!',
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    else:
        traceback.print_exception(type(error), error, error.__traceback__)

# Moderation Commands
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='You cannot kick someone with a higher or equal role!',
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title='<:kick1:1389178762020520109> Member Kicked',
            description=f'**Member:** {member.mention}\n**Reason:** {reason or "No reason provided"}\n**Moderator:** {ctx.author.mention}',
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='I do not have permission to kick this member!',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='You cannot ban someone with a higher or equal role!',
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title='<:ban1:1389180694814654474> Member Banned',
            description=f'**Member:** {member.mention}\n**Reason:** {reason or "No reason provided"}\n**Moderator:** {ctx.author.mention}',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='I do not have permission to ban this member!',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        bans = [ban_entry async for ban_entry in ctx.guild.bans()]
        for ban_entry in bans:
            if ban_entry.user.id == user_id:
                await ctx.guild.unban(user)
                embed = discord.Embed(
                    title='<:unban1:1389180853195771906> User Unbanned',
                    description=f'**User:** {user.mention}\n**Moderator:** {ctx.author.mention}',
                    color=discord.Color.green()
                )
                return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='This user is not banned!',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except discord.NotFound:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='User not found!',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount <= 0:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='Please specify a positive number!',
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            title='<:clear1:1389181036755161221> Messages Cleared',
            description=f'Successfully deleted {len(deleted)-1} messages.',
            color=discord.Color.green()
        )
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await msg.delete()
    except discord.Forbidden:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='I do not have permission to delete messages!',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command(name='warn')
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='You cannot warn someone with a higher or equal role!',
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    embed = discord.Embed(
        title='<:warn1:1389181551358509077> Member Warned',
        description=f'**Member:** {member.mention}\n**Reason:** {reason or "No reason provided"}\n**Moderator:** {ctx.author.mention}',
        color=discord.Color.yellow()
    )
    await ctx.send(embed=embed)

    try:
        warn_dm = discord.Embed(
            title='⚠️ Warning Received',
            description=f'You have been warned in {ctx.guild.name}\n**Reason:** {reason or "No reason provided"}\n**Moderator:** {ctx.author}',
            color=discord.Color.yellow()
        )
        await member.send(embed=warn_dm)
    except discord.Forbidden:
        pass

@bot.command(name='help')
async def custom_help(ctx):
    embed = discord.Embed(
        title='<:help1:1389181551358509077> Xecura Help Menu',
        description='Welcome to Xecura Bot! Choose a category below to view commands.',
        color=discord.Color.blue()
    )
    embed.add_field(
        name='Quick Tips',
        value='• Use the dropdown menu below to navigate\n• All commands start with the prefix `x!`\n• Some users may have no-prefix privileges',
        inline=False
    )
    embed.set_footer(text=f'Prefix: {DEFAULT_PREFIX} | Total Commands: {len(bot.commands)}')
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    view = HelpView()
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

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='You cannot kick someone with a higher or equal role!',
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)
    
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title='<:tick1:1389181551358509077> Member Kicked',
            description=f'{member.mention} has been kicked\nReason: {reason or "No reason provided"}',
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='I do not have permission to kick this member!',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='You cannot ban someone with a higher or equal role!',
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)
    
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title='<:tick1:1389181551358509077> Member Banned',
            description=f'{member.mention} has been banned\nReason: {reason or "No reason provided"}',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='I do not have permission to ban this member!',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        try:
            await ctx.guild.unban(user)
            embed = discord.Embed(
                title='<:tick1:1389181551358509077> User Unbanned',
                description=f'{user.mention} has been unbanned',
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.NotFound:
            embed = discord.Embed(
                title='<a:nope1:1389178762020520109> Error',
                description='This user is not banned!',
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    except discord.NotFound:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='User not found!',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount <= 0:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='Please specify a positive number!',
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)
    
    deleted = await ctx.channel.purge(limit=amount + 1)
    embed = discord.Embed(
        title='<:tick1:1389181551358509077> Messages Cleared',
        description=f'Deleted {len(deleted)-1} messages',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, delete_after=5)

@bot.command(name='warn')
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    if member.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='You cannot warn someone with a higher or equal role!',
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)
    
    embed = discord.Embed(
        title='<:tick1:1389181551358509077> Member Warned',
        description=f'{member.mention} has been warned\nReason: {reason or "No reason provided"}',
        color=discord.Color.yellow()
    )
    await ctx.send(embed=embed)
    
    try:
        warn_dm = discord.Embed(
            title='⚠️ Warning Received',
            description=f'You were warned in {ctx.guild.name}\nReason: {reason or "No reason provided"}',
            color=discord.Color.yellow()
        )
        await member.send(embed=warn_dm)
    except discord.Forbidden:
        pass

# Run the bot
bot.run(TOKEN)
