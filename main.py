import discord
from discord.ext import commands
from discord import app_commands, Interaction, SelectOption, PartialEmoji, Embed
from discord.ui import Select, View

import json
import os
import asyncio
import platform
from typing import Optional


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
            SelectOption(
                label='General',
                description='Basic utility commands',
                emoji=PartialEmoji(name='general1', id=1389183049916481646)
            ),
            SelectOption(
                label='Profile',
                description='User profile and badge management',
                emoji=PartialEmoji(name='profile1', id=1389182687947919370)
            ),
            SelectOption(
                label='Moderation',
                description='Server management commands',
                emoji=PartialEmoji(name='moderation', id=1345359844445524041)
            ),
            SelectOption(
                label='Admin',
                description='Administrative commands',
                emoji=PartialEmoji(name='GoldModerator', id=1348939969456115764)
            ),
            SelectOption(
                label='Antinuke',
                description='Server protection features',
                emoji=PartialEmoji(name='antinuke1', id=1389284381247410287)
            ),
            SelectOption(
                label='Tickets',
                description='Support ticket system',
                emoji=PartialEmoji(name='ticket1', id=1389284016099950693)
            )
        ]
        super().__init__(placeholder='✨ Select a category', options=options)

    async def callback(self, interaction: Interaction):
        try:
            category = self.values[0]
            embed = Embed(color=discord.Color.blue())
            embed.set_author(name=f'{category} Commands', icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

            if category == 'General':
                embed.description = "Here are the general utility commands:"
                embed.add_field(name='<:help:1345381592335646750> `help`', value='Show this help menu', inline=False)
                embed.add_field(name='<a:ping:1345381376433717269> `ping`', value='Check bot\'s latency', inline=False)
                embed.add_field(name='<:info:1345381592335646751> `botinfo`', value='View information about the bot', inline=False)
                embed.add_field(name='<:server:1345381592335646752> `serverinfo`', value='View information about the server', inline=False)
                embed.add_field(name='<:user:1345381592335646753> `userinfo [user]`', value='View information about a user', inline=False)

            elif category == 'Profile':
                embed.description = "Manage your profile and badges:"
                embed.add_field(name='<:profile1:1389182687947919370> `profile [user]`', value='View your or someone else\'s profile', inline=False)

            try:
                await interaction.response.edit_message(embed=embed)
            except discord.InteractionResponded:
                await interaction.message.edit(embed=embed)
        except Exception as e:
            try:
                await interaction.response.send_message(f'An error occurred: {str(e)}', ephemeral=True)
            except discord.InteractionResponded:
                await interaction.followup.send(f'An error occurred: {str(e)}', ephemeral=True)

        elif category == 'Moderation':
            embed.description = "Server moderation commands:"
            embed.add_field(name='<:kick:1345360371002900550> `kick <user> [reason]`', value='Kick a member from the server', inline=False)
            embed.add_field(name='<:ban:1345360761236488276> `ban <user> [reason]`', value='Ban a member from the server', inline=False)
            embed.add_field(name='<:unban:1345361440969724019> `unban <user_id>`', value='Unban a user from the server', inline=False)
            embed.add_field(name='<a:purge:1345361946324631644> `clear <amount>`', value='Delete a specified number of messages', inline=False)
            embed.add_field(name='<:timeout:1345362419475546173> `warn <user> [reason]`', value='Warn a member', inline=False)

        elif category == 'Admin':
            embed.description = "Owner-only administrative commands:"
            embed.add_field(name='<:badge1:1389182687947919370> `givebadge <user> <badge>`', value='Give a badge to a user', inline=False)
            embed.add_field(name='<:nobadge1:1389178762020520109> `removebadge <user> <badge>`', value='Remove a badge from a user', inline=False)
            embed.add_field(name='<:prefix1:1389181942553116695> `togglenoprefix <user>`', value='Toggle no-prefix mode for a user', inline=False)

        elif category == 'Antinuke':
            embed.description = "Server protection commands:"
            embed.add_field(name='<:antinuke1:1389284381247410287> `antinuke <enable/disable>`', value='Enable or disable server protection', inline=False)
            embed.add_field(name='<:whitelist1:1389284381247410288> `whitelist <add/remove/list> [user]`', value='Manage trusted users for antinuke', inline=False)

        elif category == 'Tickets':
            embed.description = "Ticket system commands:"
            embed.add_field(name='<:ticket1:1389284016099950693> `setup-tickets`', value='Create the ticket panel', inline=False)
            embed.add_field(name='<:settings1:1389284016099950694> `ticket-settings`', value='Configure ticket system settings', inline=False)

        embed.set_footer(text=f'Prefix: {DEFAULT_PREFIX} | Total Commands: {len(bot.commands)}')

        try:
            await interaction.response.edit_message(embed=embed)
        except discord.InteractionResponded:
            await interaction.message.edit(embed=embed)

class HelpView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpDropdown())
        self.message = None

    async def on_timeout(self):
        if self.message:
            await self.message.edit(view=None)

@bot.command(name='botinfo')
async def botinfo(ctx):
    embed = discord.Embed(
        title='<:info:1345381592335646751> Bot Information',
        color=ctx.author.color or discord.Color.blue()
    )
    embed.add_field(name='Bot Name', value=bot.user.name, inline=True)
    embed.add_field(name='Bot ID', value=bot.user.id, inline=True)
    embed.add_field(name='Created On', value=bot.user.created_at.strftime('%Y-%m-%d'), inline=True)
    embed.add_field(name='Servers', value=len(bot.guilds), inline=True)
    embed.add_field(name='Users', value=len(set(bot.get_all_members())), inline=True)
    embed.add_field(name='Commands', value=len(bot.commands), inline=True)
    embed.add_field(name='Python Version', value=platform.python_version(), inline=True)
    embed.add_field(name='Discord.py Version', value=discord.__version__, inline=True)
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    await ctx.send(embed=embed)

@bot.command(name='serverinfo')
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f'<:server:1345381592335646752> {guild.name}',
        color=ctx.author.color or discord.Color.blue()
    )
    embed.add_field(name='Server ID', value=guild.id, inline=True)
    embed.add_field(name='Owner', value=guild.owner.mention, inline=True)
    embed.add_field(name='Created On', value=guild.created_at.strftime('%Y-%m-%d'), inline=True)
    embed.add_field(name='Members', value=guild.member_count, inline=True)
    embed.add_field(name='Channels', value=len(guild.channels), inline=True)
    embed.add_field(name='Roles', value=len(guild.roles), inline=True)
    embed.add_field(name='Boost Level', value=guild.premium_tier, inline=True)
    embed.add_field(name='Boosts', value=guild.premium_subscription_count, inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

@bot.command(name='userinfo')
async def userinfo(ctx, member: Optional[discord.Member] = None):
    member = member or ctx.author
    roles = [role.mention for role in member.roles[1:]]  # All roles except @everyone
    embed = discord.Embed(
        title=f'<:user:1345381592335646753> User Information',
        color=member.color or discord.Color.blue()
    )
    embed.add_field(name='User ID', value=member.id, inline=True)
    embed.add_field(name='Nickname', value=member.nick or 'None', inline=True)
    embed.add_field(name='Account Created', value=member.created_at.strftime('%Y-%m-%d'), inline=True)
    embed.add_field(name='Joined Server', value=member.joined_at.strftime('%Y-%m-%d'), inline=True)
    embed.add_field(name='Top Role', value=member.top_role.mention, inline=True)
    embed.add_field(name='Bot?', value='Yes' if member.bot else 'No', inline=True)
    if roles:
        embed.add_field(name=f'Roles [{len(roles)}]', value=' '.join(roles) if len(' '.join(roles)) <= 1024 else f'{len(roles)} roles', inline=False)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    print(f'{bot.user} is ready!')
    await bot.change_presence(activity=discord.Game(name=f"Xecura | x!help"))

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
            title='<:kick:1345360371002900550> Member Kicked',
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
                    title='<:unban:1345361440969724019> User Unbanned',
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
            title='<a:purge:1345361946324631644> Messages Cleared',
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
        title='<:help:1345381592335646750> Xecura Help Menu',
        description=f'Hello {ctx.author.mention}! Welcome to Xecura Bot!\n\n**About Xecura**\nXecura is a versatile Discord bot that provides moderation, profile management, antinuke protection, and ticket system features.\n\n**Using the Bot**\n• All commands start with `{DEFAULT_PREFIX}` (some users have no-prefix privilege)\n• Use the dropdown menu below to explore different command categories\n• For detailed command usage, include the command in the help menu',
        color=ctx.author.color or discord.Color.blue()
    )
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    view = HelpView()
    message = await ctx.send(embed=embed, view=view)
    view.message = message

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
        return await ctx.send('<a:nope1:1389178762020520109> Only the bot owner can use this command!')
    
    if badge not in BADGES or badge == 'no_badge':
        return await ctx.send('<a:nope1:1389178762020520109> Invalid badge!')
    
    user_id = str(user.id)
    if user_id not in data_manager.badges:
        data_manager.badges[user_id] = set()
    
    if badge not in data_manager.badges[user_id]:
        data_manager.badges[user_id].add(badge)
        data_manager.save_data()
        await ctx.send(f'<:tick1:1389181551358509077> Added {BADGES[badge]} to {user.mention}')
    else:
        await ctx.send(f'<a:nope1:1389178762020520109> {user.mention} already has this badge!')

@bot.command(name='removebadge')
async def remove_badge(ctx, user: discord.Member, badge: str):
    if ctx.author.id != OWNER_ID:
        return await ctx.send('<a:nope1:1389178762020520109> Only the bot owner can use this command!')
    
    user_id = str(user.id)
    if user_id in data_manager.badges and badge in data_manager.badges[user_id]:
        data_manager.badges[user_id].remove(badge)
        if not data_manager.badges[user_id]:  # Remove empty set
            del data_manager.badges[user_id]
        data_manager.save_data()
        await ctx.send(f'<:tick1:1389181551358509077> Removed {BADGES[badge]} from {user.mention}')
    else:
        await ctx.send(f'<a:nope1:1389178762020520109> {user.mention} doesn\'t have this badge!')

@bot.command(name='togglenoprefix')
async def toggle_no_prefix(ctx, user: discord.Member):
    if ctx.author.id != OWNER_ID:
        return await ctx.send('<a:nope1:1389178762020520109> Only the bot owner can use this command!')
    
    user_id = str(user.id)
    if user_id in data_manager.no_prefix_users:
        data_manager.no_prefix_users.remove(user_id)
        status = 'disabled'
    else:
        data_manager.no_prefix_users.add(user_id)
        status = 'enabled'
    
    data_manager.save_data()
    embed = discord.Embed(
        title='<:prefix1:1389181942553116695> No-Prefix Status Updated',
        description=f'No-prefix mode has been {status} for {user.mention}',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# Antinuke System
class AntinukeManager:
    def __init__(self):
        self.enabled_guilds = set()
        self.whitelisted_users = {}
        self.load_data()
    
    def load_data(self):
        try:
            with open('antinuke.json', 'r') as f:
                data = json.load(f)
                self.enabled_guilds = set(data.get('enabled_guilds', []))
                self.whitelisted_users = {guild_id: set(users) for guild_id, users in data.get('whitelisted_users', {}).items()}
        except FileNotFoundError:
            self.save_data()
    
    def save_data(self):
        with open('antinuke.json', 'w') as f:
            json_data = {
                'enabled_guilds': list(self.enabled_guilds),
                'whitelisted_users': {guild_id: list(users) for guild_id, users in self.whitelisted_users.items()}
            }
            json.dump(json_data, f, indent=4)

antinuke_manager = AntinukeManager()

@bot.command(name='whitelist')
@commands.has_permissions(administrator=True)
async def whitelist(ctx, action: str, member: Optional[discord.Member] = None):
    guild_id = str(ctx.guild.id)
    
    if action.lower() not in ['add', 'remove', 'list']:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='Invalid action! Use `add`, `remove`, or `list`.',
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)
    
    if action.lower() != 'list' and not member:
        embed = discord.Embed(
            title='<a:nope1:1389178762020520109> Error',
            description='Please specify a member to add/remove from whitelist!',
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)
    
    if guild_id not in antinuke_manager.whitelisted_users:
        antinuke_manager.whitelisted_users[guild_id] = set()
    
    if action.lower() == 'list':
        whitelisted = antinuke_manager.whitelisted_users[guild_id]
        if not whitelisted:
            description = 'No users are whitelisted in this server.'
        else:
            users = ['<@' + user_id + '>' for user_id in whitelisted]
            description = '**Whitelisted Users:**\n' + '\n'.join(users)
        
        embed = discord.Embed(
            title='✅ Whitelist',
            description=description,
            color=discord.Color.blue()
        )
        return await ctx.send(embed=embed)
    
    member_id = str(member.id)
    if action.lower() == 'add':
        antinuke_manager.whitelisted_users[guild_id].add(member_id)
        status = 'added to'
    else:
        antinuke_manager.whitelisted_users[guild_id].discard(member_id)
        status = 'removed from'
    
    antinuke_manager.save_data()
    embed = discord.Embed(
        title='✅ Whitelist Updated',
        description=f'{member.mention} has been {status} the whitelist.',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# Ticket System
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='Close Ticket', style=discord.ButtonStyle.danger, emoji='🔒', custom_id='close_ticket')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = str(interaction.guild.id)
        channel_id = str(interaction.channel.id)
        
        try:
            with open(f'tickets/{guild_id}.json', 'r') as f:
                data = json.load(f)
                if channel_id in data['tickets']:
                    ticket_data = data['tickets'][channel_id]
                    creator_id = ticket_data['creator']
                    
                    if interaction.user.guild_permissions.administrator or interaction.user.id == creator_id:
                        embed = discord.Embed(
                            title='🔒 Ticket Closed',
                            description=f'This ticket was closed by {interaction.user.mention}.',
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed)
                        await asyncio.sleep(5)
                        await interaction.channel.delete()
                        
                        del data['tickets'][channel_id]
                        with open(f'tickets/{guild_id}.json', 'w') as f:
                            json.dump(data, f, indent=4)
                    else:
                        await interaction.response.send_message('You do not have permission to close this ticket!', ephemeral=True)
        except FileNotFoundError:
            await interaction.response.send_message('Error: Ticket data not found!', ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='Create Ticket', style=discord.ButtonStyle.primary, emoji='🎫', custom_id='create_ticket')
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = str(interaction.guild.id)
        if not os.path.exists('tickets'):
            os.makedirs('tickets')
        
        try:
            with open(f'tickets/{guild_id}.json', 'r') as f:
                data = json.load(f)
                ticket_number = data.get('last_ticket', 0) + 1
        except FileNotFoundError:
            ticket_number = 1
            data = {'last_ticket': 0, 'tickets': {}}
        
        channel_name = f'ticket-{ticket_number:04d}'
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=interaction.channel.category,
            overwrites=overwrites
        )
        
        embed = discord.Embed(
            title='🎫 Ticket Created',
            description=f'Welcome {interaction.user.mention}!\nSupport will be with you shortly.\n\nClick the button below to close this ticket when resolved.',
            color=discord.Color.blue()
        )
        close_view = CloseTicketView()
        await channel.send(embed=embed, view=close_view)
        
        data['last_ticket'] = ticket_number
        data['tickets'][str(channel.id)] = {
            'creator': interaction.user.id,
            'created_at': discord.utils.utcnow().isoformat()
        }
        
        with open(f'tickets/{guild_id}.json', 'w') as f:
            json.dump(data, f, indent=4)
        
        await interaction.response.send_message(f'Your ticket has been created: {channel.mention}', ephemeral=True)


@bot.command(name='ticket-settings')
@commands.has_permissions(administrator=True)
async def ticket_settings(ctx):
    embed = discord.Embed(
        title='📝 Ticket Settings',
        description='Ticket system settings will be available soon!',
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# Antinuke System
class AntinukeManager:
    def __init__(self):
        self.enabled_guilds = set()
        self.whitelisted_users = {}
        self.load_data()
    
    def load_data(self):
        try:
            with open('antinuke.json', 'r') as f:
                data = json.load(f)
                self.enabled_guilds = set(data.get('enabled_guilds', []))
                self.whitelisted_users = {guild_id: set(users) for guild_id, users in data.get('whitelisted_users', {}).items()}
        except FileNotFoundError:
            self.save_data()
    
    def save_data(self):
        with open('antinuke.json', 'w') as f:
            json_data = {
                'enabled_guilds': list(self.enabled_guilds),
                'whitelisted_users': {guild_id: list(users) for guild_id, users in self.whitelisted_users.items()}
            }
            json.dump(json_data, f, indent=4)

antinuke_manager = AntinukeManager()

# Antinuke Event Listeners
@bot.event
async def on_member_ban(guild, user):
    guild_id = str(guild.id)
    if guild_id not in antinuke_manager.enabled_guilds:
        return

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if str(entry.user.id) not in antinuke_manager.whitelisted_users.get(guild_id, set()):
            try:
                await guild.unban(user, reason='Antinuke: Unauthorized ban')
                await entry.user.ban(reason='Antinuke: Unauthorized ban action')
            except discord.Forbidden:
                pass

@bot.event
async def on_member_remove(member):
    guild = member.guild
    guild_id = str(guild.id)
    if guild_id not in antinuke_manager.enabled_guilds:
        return

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        if str(entry.user.id) not in antinuke_manager.whitelisted_users.get(guild_id, set()):
            try:
                await entry.user.ban(reason='Antinuke: Unauthorized kick action')
            except discord.Forbidden:
                pass

@bot.event
async def on_guild_channel_delete(channel):
    guild = channel.guild
    guild_id = str(guild.id)
    if guild_id not in antinuke_manager.enabled_guilds:
        return

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        if str(entry.user.id) not in antinuke_manager.whitelisted_users.get(guild_id, set()):
            try:
                await entry.user.ban(reason='Antinuke: Unauthorized channel deletion')
            except discord.Forbidden:
                pass

@bot.event
async def on_guild_role_delete(role):
    guild = role.guild
    guild_id = str(guild.id)
    if guild_id not in antinuke_manager.enabled_guilds:
        return

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        if str(entry.user.id) not in antinuke_manager.whitelisted_users.get(guild_id, set()):
            try:
                await entry.user.ban(reason='Antinuke: Unauthorized role deletion')
            except discord.Forbidden:
                pass

@bot.command(name='antinuke')
@commands.has_permissions(administrator=True)
async def antinuke(ctx, action: str = None):
    if action is None:
        status = 'enabled' if str(ctx.guild.id) in antinuke_manager.enabled_guilds else 'disabled'
        embed = discord.Embed(
            title='<:shield:1345382219774087168> Antinuke Status',
            description=f'Antinuke is currently **{status}** for this server.',
            color=discord.Color.blue()
        )
        return await ctx.send(embed=embed)
    
    if action.lower() not in ['enable', 'disable']:
        return await ctx.send('<a:nope1:1389178762020520109> Invalid action! Use `enable` or `disable`.')
    
    guild_id = str(ctx.guild.id)
    if action.lower() == 'enable':
        antinuke_manager.enabled_guilds.add(guild_id)
        msg = 'enabled'
    else:
        antinuke_manager.enabled_guilds.discard(guild_id)
        msg = 'disabled'
    
    antinuke_manager.save_data()
    embed = discord.Embed(
        title='<:shield:1345382219774087168> Antinuke Updated',
        description=f'Antinuke has been {msg} for this server.',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# Ticket System
class TicketManager:
    def __init__(self):
        self.tickets = {}
        self.load_data()
    
    def load_data(self):
        try:
            with open('tickets.json', 'r') as f:
                self.tickets = json.load(f)
        except FileNotFoundError:
            self.save_data()
    
    def save_data(self):
        with open('tickets.json', 'w') as f:
            json.dump(self.tickets, f, indent=4)

ticket_manager = TicketManager()

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='Create Ticket', style=discord.ButtonStyle.green, emoji='🎫')
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = str(interaction.guild.id)
        if guild_id not in ticket_manager.tickets:
            ticket_manager.tickets[guild_id] = {'count': 0, 'active': {}}
        
        ticket_data = ticket_manager.tickets[guild_id]
        ticket_data['count'] += 1
        ticket_number = ticket_data['count']
        
        # Create ticket channel
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        channel = await interaction.guild.create_text_channel(
            f'ticket-{ticket_number}',
            overwrites=overwrites,
            reason=f'Ticket created by {interaction.user}'
        )
        
        ticket_data['active'][str(channel.id)] = {
            'user_id': str(interaction.user.id),
            'number': ticket_number,
            'created_at': discord.utils.utcnow().isoformat()
        }
        ticket_manager.save_data()
        
        embed = discord.Embed(
            title='🎫 Ticket Created',
            description=f'Welcome {interaction.user.mention}!\nSupport will be with you shortly.\n\nTicket: #{ticket_number}',
            color=discord.Color.green()
        )
        
        class CloseButton(View):
            def __init__(self):
                super().__init__(timeout=None)
            
            @discord.ui.button(label='Close Ticket', style=discord.ButtonStyle.red, emoji='🔒')
            async def close_ticket(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                await channel.delete()
                del ticket_data['active'][str(channel.id)]
                ticket_manager.save_data()
        
        await channel.send(embed=embed, view=CloseButton())
        await interaction.response.send_message(f'Your ticket has been created: {channel.mention}', ephemeral=True)

@bot.command(name='setup-tickets')
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    embed = discord.Embed(
        title='🎫 Create a Ticket',
        description='Click the button below to create a support ticket.',
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketView())

# Update help menu with new categories
class HelpDropdown(Select):
    def __init__(self):
        options = [
            SelectOption(
                label='General',
                description='Basic utility commands',
                emoji=PartialEmoji(name='general1', id=1389183049916481646)
            ),
            SelectOption(
                label='Profile',
                description='User profile and badge management',
                emoji=PartialEmoji(name='profile1', id=1389182687947919370)
            ),
            SelectOption(
                label='Moderation',
                description='Server management commands',
                emoji=PartialEmoji(name='moderation', id=1345359844445524041)
            ),
            SelectOption(
                label='Admin',
                description='Administrative commands',
                emoji=PartialEmoji(name='GoldModerator', id=1348939969456115764)
            ),
            SelectOption(
                label='Antinuke',
                description='Server protection commands',
                emoji=PartialEmoji(name='antinuke1', id=1389284381247410287)
            ),
            SelectOption(
                label='Tickets',
                description='Ticket system commands',
                emoji=PartialEmoji(name='ticket1', id=1389284016099950693)
            )
        ]
        super().__init__(placeholder='✨ Select a category', options=options)

@bot.command(name='ping')
async def ping(ctx):
    embed = discord.Embed(
        title='<a:ping:1345381376433717269> Pong!',
        description=f'Latency: {round(bot.latency * 1000)}ms',
        color=discord.Color.green()
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



# Run the bot
bot.run(TOKEN)
