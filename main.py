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
                emoji='<:profile1:1389287397761745039>'
            ),
            discord.SelectOption(
                label='Moderation',
                description='Server management commands',
                emoji='<:moderation:1345359844445524041>'
            ),
            discord.SelectOption(
                label='Admin',
                description='Administrative commands',
                emoji='<:GoldModerator:1348939969456115764>'
            ),
            discord.SelectOption(
                label='Antinuke',
                description='Server protection commands',
                emoji='<:antinuke1:1389284381247410287>'
            ),
            discord.SelectOption(
                label='Tickets',
                description='Ticket system commands',
                emoji='<:ticket1:1389284016099950693>'
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
                name='<:help:1345381592335646750> `help`',
                value='Show this help menu',
                inline=False
            )
            embed.add_field(
                name='<a:ping:1345381376433717269> `ping`',
                value='Check bot\'s latency',
                inline=False
            )
        
        elif category == 'Profile':
            embed.description = "Manage your profile and badges:"
            embed.add_field(
                name='<:profile1:1389287397761745039> `profile [user]`',
                value='View your or someone else\'s profile',
                inline=False
            )
        
        elif category == 'Moderation':
            embed.description = "Server moderation commands:"
            embed.add_field(
                name='<:kick:1345360371002900550> `kick <user> [reason]`',
                value='Kick a member from the server',
                inline=False
            )
            embed.add_field(
                name='<:ban:1345360761236488276> `ban <user> [reason]`',
                value='Ban a member from the server',
                inline=False
            )
            embed.add_field(
                name='<:unban:1345361440969724019> `unban <user_id>`',
                value='Unban a user from the server',
                inline=False
            )
            embed.add_field(
                name='<a:purge:1345361946324631644> `clear <amount>`',
                value='Delete a specified number of messages',
                inline=False
            )
            embed.add_field(
                name='<:timeout:1345362419475546173> `warn <user> [reason]`',
                value='Warn a member',
                inline=False
            )
        
        elif category == 'Admin':
            embed.description = "Owner-only administrative commands:"
            embed.add_field(
                name='<a:badge1:1389182687947919370> `givebadge <user> <badge>`',
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

@bot.command(name='whitelist')
@commands.has_permissions(administrator=True)
async def whitelist(ctx, action: str, user: discord.Member = None):
    if action.lower() not in ['add', 'remove', 'list']:
        return await ctx.send('<a:nope1:1389178762020520109> Invalid action! Use `add`, `remove`, or `list`.')
    
    guild_id = str(ctx.guild.id)
    if guild_id not in antinuke_manager.whitelisted_users:
        antinuke_manager.whitelisted_users[guild_id] = set()
    
    if action.lower() == 'list':
        users = antinuke_manager.whitelisted_users[guild_id]
        if not users:
            return await ctx.send('<a:nope1:1389178762020520109> No whitelisted users in this server.')
        
        whitelisted = '\n'.join([f'<@{user_id}>' for user_id in users])
        embed = discord.Embed(
            title='<:shield:1345382219774087168> Whitelisted Users',
            description=whitelisted,
            color=discord.Color.blue()
        )
        return await ctx.send(embed=embed)
    
    if not user:
        return await ctx.send('<a:nope1:1389178762020520109> Please specify a user!')
    
    if action.lower() == 'add':
        antinuke_manager.whitelisted_users[guild_id].add(str(user.id))
        msg = f'{user.mention} has been whitelisted.'
    else:
        antinuke_manager.whitelisted_users[guild_id].discard(str(user.id))
        msg = f'{user.mention} has been removed from the whitelist.'
    
    antinuke_manager.save_data()
    await ctx.send(f'<:tick1:1389181551358509077> {msg}')

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
