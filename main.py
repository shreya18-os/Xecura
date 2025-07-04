import discord
from discord.ext import commands
from discord import app_commands, Interaction, SelectOption, PartialEmoji, Embed
from discord.ui import Select, View
import traceback
import json
import os
import asyncio
import platform
import datetime
import sqlite3
from typing import Optional


# Initialize bot configuration
DEFAULT_PREFIX = 'x!'
OWNER_ID = 1101467683083530331

# Load bot token from environment variable (Railway secrets)
TOKEN = os.getenv('BOT_TOKEN')

# Create bot instance with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=DEFAULT_PREFIX, intents=intents, help_command=None)

# Define available badges
BADGES = {
    'owner': '<:owner1:1389180694814654474>',
    'admin': '<:admin1:1389181036755161221>',
    'staff': '<a:staff112:1389180853195771906>',
    'bug_hunter': '<:bughn1:1389618460606206002>',
    'moderator': '<:Management:1348937775554105355>',
    'vip': '<:vip1:1389618245803446302>',
    'no_badge': '<a:nope1:1389178762020520109>'
}

# Initialize data storage
# Get data directory from environment variable or use current directory as fallback
DATA_DIR = os.getenv('XECURA_DATA_DIR', os.getcwd())

class DataManager:
    def verify_database_access(self) -> bool:
        try:
            print(f'[DEBUG] Verifying database access at {self.db_file}')
            if not os.path.exists(self.data_dir):
                print(f'[ERROR] Data directory does not exist: {self.data_dir}')
                return False
            if not os.access(self.data_dir, os.W_OK):
                print(f'[ERROR] Data directory is not writable: {self.data_dir}')
                return False
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()
            if not os.access(self.db_file, os.W_OK):
                print(f'[ERROR] Database file is not writable: {self.db_file}')
                return False
            print('[DEBUG] Database access verified successfully')
            return True
        except Exception as e:
            print(f'[ERROR] Database access verification failed: {str(e)}')
            traceback.print_exc()
            return False

    def __init__(self):
        self.badges = {}
        self.no_prefix_users = set()
        self.data_dir = os.getenv('DATA_DIR', os.path.abspath(os.path.join(os.getcwd(), 'data')))
        print(f'[DEBUG] Using data directory: {self.data_dir}')
        try:
            os.makedirs(self.data_dir, mode=0o777, exist_ok=True)
            print(f'[DEBUG] Created/verified data directory at {self.data_dir}')
        except Exception as e:
            print(f'[DEBUG] Error creating data directory: {str(e)}')
            raise
        self.db_file = os.path.join(self.data_dir, 'data.db')
        print(f'[DEBUG] Database file path: {self.db_file}')
        if not self.verify_database_access():
            raise Exception('Database access verification failed')

        max_retries = 3
        retry_delay = 1  # seconds
        for attempt in range(max_retries):
            try:
                self.init_database()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f'[DEBUG] Database initialization attempt {attempt + 1} failed, retrying in {retry_delay} seconds...')
                time.sleep(retry_delay)
                retry_delay *= 2

        for attempt in range(max_retries):
            try:
                self.load_data()
                if self.verify_data_consistency():
                    break
                raise Exception('Data consistency check failed')
            except Exception as e:
                if attempt == max_retries - 1:
                    print('[DEBUG] All load attempts failed, initializing empty data')
                    self.badges = {}
                    self.no_prefix_users = set()
                    break
                print(f'[DEBUG] Data load attempt {attempt + 1} failed, retrying in {retry_delay} seconds...')
                time.sleep(retry_delay)
                retry_delay *= 2

    async def start_auto_save(self):
        asyncio.create_task(self._auto_save_loop())

    async def _auto_save_loop(self):
        while True:
            try:
                await asyncio.sleep(300)  # Save every 5 minutes
                print('[DEBUG] Running auto-save...')
                self.save_data()
                if not self.verify_data_consistency():
                    print('[WARNING] Data consistency check failed after auto-save')
            except Exception as e:
                print(f'[ERROR] Auto-save failed: {str(e)}')
                traceback.print_exc()

    def init_database(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS badges (
                    user_id TEXT PRIMARY KEY,
                    badges TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS no_prefix_users (
                    user_id TEXT PRIMARY KEY
                )
            ''')
            conn.commit()

    def load_data(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, badges FROM badges')
            for user_id, badges_str in cursor.fetchall():
                self.badges[user_id] = set(badges_str.split(','))
            
            cursor.execute('SELECT user_id FROM no_prefix_users')
            self.no_prefix_users = set(row[0] for row in cursor.fetchall())

    def save_data(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM badges')
            cursor.execute('DELETE FROM no_prefix_users')
            
            for user_id, badges in self.badges.items():
                cursor.execute('INSERT INTO badges VALUES (?, ?)', (user_id, ','.join(badges)))
            
            for user_id in self.no_prefix_users:
                cursor.execute('INSERT INTO no_prefix_users VALUES (?)', (user_id,))
            
            conn.commit()

    def verify_data_consistency(self) -> bool:
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM badges')
                db_badge_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM no_prefix_users')
                db_noprefix_count = cursor.fetchone()[0]
                
                if db_badge_count != len(self.badges) or db_noprefix_count != len(self.no_prefix_users):
                    print(f'[DEBUG] Data consistency mismatch:\nBadges: DB={db_badge_count}, Memory={len(self.badges)}\nNo-prefix: DB={db_noprefix_count}, Memory={len(self.no_prefix_users)}')
                    return False
                return True
        except Exception as e:
            print(f'[DEBUG] Data consistency check failed: {str(e)}')
            return False

# Initialize the data manager instance
data_manager = DataManager()

@bot.event
async def on_ready():
    print(f'{bot.user} is ready!')
    await bot.change_presence(activity=discord.Game(name=f"Xecura | x!help"))
    await data_manager.start_auto_save()

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

class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='General', description='General utility commands', emoji='<:help:1345381592335646750>'),
            discord.SelectOption(label='Profile', description='Profile and badge commands', emoji='<:profile1:1389287397761745039>'),
            discord.SelectOption(label='Moderation', description='Server moderation commands', emoji='<:kick:1345360371002900550>'),
            discord.SelectOption(label='Utility', description='Additional utility commands', emoji='<:role1:1389607749985370255>'),
            discord.SelectOption(label='Antinuke', description='Server protection commands', emoji='<:antinuke1:1389284381247410287>'),
            discord.SelectOption(label='Tickets', description='Ticket system commands', emoji='<:ticket1:1389284016099950693>'),
            discord.SelectOption(label='Admin', description='Owner-only commands', emoji='<:badge1:1389589621872136293>')
        ]
        super().__init__(placeholder='Select a category...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        try:
            await interaction.response.defer()
            
            category = self.values[0]
            embed = Embed(color=discord.Color.blue())
            embed.set_author(name=f'{category} Commands', icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

            if category == 'General':
                embed.description = "Here are the general utility commands:"
                embed.add_field(name='<:help:1345381592335646750> `help`', value='Show this help menu', inline=False)
                embed.add_field(name='<a:ping:1345381376433717269> `ping`', value='Check bot\'s latency', inline=False)
                embed.add_field(name='<:rinvites:1345380642342572193> `botinfo`', value='View information about the bot', inline=False)
                embed.add_field(name='<:server1:1389588267808325632> `serverinfo`', value='View information about the server', inline=False)
                embed.add_field(name='<:profile1:1389287397761745039> `userinfo [user]`', value='View information about a user', inline=False)
                embed.add_field(name='<:avatar1:1389603923316441199> `avatar [user]`', value='View user\'s avatar', inline=False)
                embed.add_field(name='<:server1:1389588267808325632> `servericon`', value='View server\'s icon', inline=False)
                embed.add_field(name='<:members1:1389604287469977691> `members`', value='View server member statistics', inline=False)

            elif category == 'Profile':
                embed.description = "Manage your profile and badges:"
                embed.add_field(name='<:profile1:1389287397761745039> `profile [user]`', value='View your or someone else\'s profile', inline=False)

            elif category == 'Moderation':
                embed.description = "Server moderation commands:"
                embed.add_field(name='<:kick:1345360371002900550> `kick <user> [reason]`', value='Kick a member from the server', inline=False)
                embed.add_field(name='<:ban:1345360761236488276> `ban <user> [reason]`', value='Ban a member from the server', inline=False)
                embed.add_field(name='<:unban:1345361440969724019> `unban <user_id>`', value='Unban a user from the server', inline=False)
                embed.add_field(name='<a:purge:1345361946324631644> `clear <amount>`', value='Delete a specified number of messages', inline=False)
                embed.add_field(name='<:timeout:1345362419475546173> `warn <user> [reason]`', value='Warn a member', inline=False)
                embed.add_field(name='<:slowmode1:1389604723610619984> `slowmode <seconds>`', value='Set channel slowmode', inline=False)
                embed.add_field(name='<a:nickname1:1389605067622977579> `nickname <user> [new_nick]`', value='Change user\'s nickname', inline=False)
                embed.add_field(name='<:mute1:1389605413132963951> `mute <user> <duration> [reason]`', value='Timeout a user', inline=False)
                embed.add_field(name='<:unmute1:1389605655622717551> `unmute <user>`', value='Remove timeout from a user', inline=False)

            elif category == 'Utility':
                embed.description = "Additional utility commands:"
                embed.add_field(name='<:role1:1389607749985370255> `role <user> <role>`', value='Add/remove role from user', inline=False)
                embed.add_field(name='<:invites:1345380333222367285> `createchannel <name> [type]`', value='Create a new channel', inline=False)
                embed.add_field(name='<:delch1:1389608102583603262> `deletechannel <channel>`', value='Delete a channel', inline=False)
                embed.add_field(name='<:rinvites:1345380642342572193> `invites`', value='List all server invites', inline=False)
                embed.add_field(name='<:lock1:1389608483292450827> `lock [channel]`', value='Lock a channel', inline=False)
                embed.add_field(name='<:unlock1:1389608708073590819> `unlock [channel]`', value='Unlock a channel', inline=False)

            elif category == 'Antinuke':
                embed.description = "Server protection commands:"
                embed.add_field(name='<:antinuke1:1389284381247410287> `antinuke <enable/disable>`', value='Enable or disable server protection', inline=False)
                embed.add_field(name='<:whitelist:1389590639343308896> `whitelist <add/remove/list> [user]`', value='Manage trusted users for antinuke', inline=False)

            elif category == 'Tickets':
                embed.description = "Ticket system commands:"
                embed.add_field(name='<:ticket1:1389284016099950693> `setup-tickets`', value='Create the ticket panel', inline=False)
                embed.add_field(name='<a:setting1:1389590399760334868> `ticket-settings`', value='Configure ticket system settings', inline=False)

            elif category == 'Admin':
                embed.description = "Owner-only administrative commands:"
                embed.add_field(name='<:badge1:1389589621872136293> `givebadge <user> <badge>`', value='Give a badge to a user (Available badges: owner, admin, staff, bug_hunter, moderator, vip)', inline=False)
                embed.add_field(name='<:prefix1:1389181942553116695> `togglenoprefix [user]`', value='Toggle no-prefix mode for a user', inline=False)

            embed.set_footer(text=f'Prefix: {DEFAULT_PREFIX} | Total Commands: {len(bot.commands)}')
            await interaction.edit_original_response(embed=embed)

        except Exception as e:
            try:
                await interaction.followup.send(f'An error occurred while updating the help menu: {str(e)}', ephemeral=True)
            except:
                pass

class HelpView(View):
    def __init__(self):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.add_item(HelpDropdown())
        self.message = None

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except:
            pass

@bot.command(name='botinfo')
async def botinfo(ctx):
    embed = discord.Embed(
        title='<:rinvites:1345380642342572193> Bot Information',
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
        title=f'<:server1:1389588267808325632> {guild.name}',
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
        title=f'<:profile1:1389287397761745039> User Information',
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

@bot.command(name='help', aliases=['h'])
async def custom_help(ctx):
    embed = discord.Embed(
        title='<:help:1345381592335646750> Xecura Help Menu',
        description=f'Hello {ctx.author.mention}! Welcome to Xecura Bot!\n\n**About Xecura**\nXecura is a versatile Discord bot that provides moderation, profile management, antinuke protection, and ticket system features.\n\n**Using the Bot**\n• All commands start with `{DEFAULT_PREFIX}` (some users have no-prefix privilege)\n• Use the dropdown menu below to explore different command categories\n• For detailed command usage, include the command in the help menu',
        color=ctx.author.color or discord.Color.blue()
    )
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    view = HelpView()
    view.message = await ctx.send(embed=embed, view=view)

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
                               .replace('⭐', '<:vip1:1389618245803446302>')\
                               .replace('🔨', '<:Management:1348937775554105355>')\
                               .replace('🐛', '<:bughn1:1389618460606206002>')\
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

@bot.command(name='togglenoprefix')
async def togglenoprefix(ctx, user: discord.Member):
    try:
        if ctx.author.id != OWNER_ID:  # Compare integers instead of strings
            await ctx.send('<a:nope1:1389178762020520109> Only the bot owner can use this command!')
            return

        user_id = str(user.id)
        await ctx.send('<a:time:1345383309458538518> Toggling no-prefix status...')

        if user_id in data_manager.no_prefix_users:
            data_manager.no_prefix_users.remove(user_id)
            action = 'removed from'
        else:
            data_manager.no_prefix_users.add(user_id)
            action = 'added to'

        print(f'[DEBUG] Before save - no_prefix_users: {data_manager.no_prefix_users}')
        data_manager.save_data()
        print(f'[DEBUG] After save - no_prefix_users: {data_manager.no_prefix_users}')

        # Verify data was saved correctly
        if not data_manager.verify_data_consistency():
            await ctx.send('⚠️ Warning: Data might not have been saved correctly. Please try again.')
            return

        await ctx.send(f'<:tick1:1389181551358509077> Successfully {action} no-prefix list for {user.name}!')

    except Exception as e:
        print(f'[DEBUG] Error in togglenoprefix command: {str(e)}')
        traceback.print_exc()
        await ctx.send('❌ An error occurred while processing the command.')

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
            title='<:ticket1:1389284016099950693> Ticket Created',
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
        title='<:ticket1:1389284016099950693> Create a Ticket',
        description='Click the button below to create a support ticket.',
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketView())

# Update help menu with new categories
# Help menu implementation moved to the top of the file

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

# New General Commands
@bot.command(name='avatar')
async def avatar(ctx, member: Optional[discord.Member] = None):
    member = member or ctx.author
    embed = discord.Embed(
        title=f'{member.name}\'s Avatar',
        color=member.color
    )
    embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name='servericon')
async def servericon(ctx):
    if not ctx.guild.icon:
        return await ctx.send('<a:nope1:1389178762020520109> This server has no icon!')
    embed = discord.Embed(
        title=f'{ctx.guild.name}\'s Icon',
        color=discord.Color.blue()
    )
    embed.set_image(url=ctx.guild.icon.url)
    await ctx.send(embed=embed)

@bot.command(name='members')
async def members(ctx):
    total = len(ctx.guild.members)
    humans = len([m for m in ctx.guild.members if not m.bot])
    bots = len([m for m in ctx.guild.members if m.bot])
    embed = discord.Embed(
        title=f'{ctx.guild.name} Member Stats',
        description=f'<:members1:1389604287469977691> Total Members: {total}\nHumans: {humans}\nBots: {bots}',
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# New Moderation Commands
@bot.command(name='slowmode')
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    if seconds < 0 or seconds > 21600:
        return await ctx.send('<a:nope1:1389178762020520109> Slowmode must be between 0 and 21600 seconds!')
    await ctx.channel.edit(slowmode_delay=seconds)
    embed = discord.Embed(
        title='<:tick1:1389181551358509077> Slowmode Updated',
        description=f'<:slowmode1:1389604723610619984>Set slowmode to {seconds} seconds',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='nickname')
@commands.has_permissions(manage_nicknames=True)
async def nickname(ctx, member: discord.Member, *, new_nick=None):
    try:
        await member.edit(nick=new_nick)
        embed = discord.Embed(
            title='<:tick1:1389181551358509077> Nickname Updated',
            description=f'Changed {member.mention}\'s nickname to: {new_nick or "Reset to default"}',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send('<a:nope1:1389178762020520109> I cannot change that member\'s nickname!')


@bot.command(name='unmute')
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        embed = discord.Embed(
            title='<:tick1:1389181551358509077> Member Unmuted',
            description=f'{member.mention} has been unmuted',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send('<a:nope1:1389178762020520109> I cannot unmute that member!')

# New Utility Commands
@bot.command(name='role')
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, *, role: discord.Role):
    if role >= ctx.author.top_role:
        return await ctx.send('<a:nope1:1389178762020520109> You cannot manage a role higher than your own!')
    if role in member.roles:
        await member.remove_roles(role)
        action = 'removed from'
    else:
        await member.add_roles(role)
        action = 'added to'
    embed = discord.Embed(
        title='<:tick1:1389181551358509077> Role Updated',
        description=f'Role {role.mention} has been {action} {member.mention}',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='createchannel')
@commands.has_permissions(manage_channels=True)
async def createchannel(ctx, channel_name, channel_type='text'):
    if channel_type.lower() not in ['text', 'voice']:
        return await ctx.send('<a:nope1:1389178762020520109> Invalid channel type! Use \'text\' or \'voice\'')
    channel_type_obj = discord.ChannelType.text if channel_type.lower() == 'text' else discord.ChannelType.voice
    channel = await ctx.guild.create_channel(name=channel_name, type=channel_type_obj)
    embed = discord.Embed(
        title='<:tick1:1389181551358509077> Channel Created',
        description=f'Created new {channel_type} channel: {channel.mention}',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='deletechannel')
@commands.has_permissions(manage_channels=True)
async def deletechannel(ctx, channel: discord.TextChannel):
    await channel.delete()
    embed = discord.Embed(
        title='<:tick1:1389181551358509077> Channel Deleted',
        description=f'Channel {channel.name} has been deleted',
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)



@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check if user has no-prefix privilege
    has_no_prefix = str(message.author.id) in data_manager.no_prefix_users

    # Process commands with or without prefix based on user's status
if has_no_prefix:
    ctx = await bot.get_context(message)
    if ctx.command is None:
        # Try to find the command without prefix
        command_name = message.content.split()[0].lower()
        command = bot.get_command(command_name)
        if command:
            message.content = f"{DEFAULT_PREFIX}{message.content}"
            await bot.process_commands(message)
            return

    await bot.process_commands(message)
    await ctx.send(embed=embed)  # Safe: ctx is defined

else:
    await bot.process_commands(message)
    # Optional: If you want to send the embed here too
    # ctx = await bot.get_context(message)
    # await ctx.send(embed=embed)


    try:
        warn_dm = discord.Embed(
            title='⚠️ Warning Received',
            description=f'You have been warned in {ctx.guild.name}\n**Reason:** {reason or "No reason provided"}\n**Moderator:** {ctx.author}',
            color=discord.Color.yellow()
        )
        await member.send(embed=warn_dm)
    except discord.Forbidden:
        pass



@bot.command(name='givebadge')
async def givebadge(ctx, user: discord.Member, badge: str):
    try:
        if ctx.author.id != OWNER_ID:  # Compare integers directly
            await ctx.send('<a:nope1:1389178762020520109> Only the bot owner can use this command!')
            return

        if badge not in BADGES.keys():  # Use BADGES dictionary keys
            await ctx.send('<a:nope1:1389178762020520109> Invalid badge type!')
            return

        user_id = str(user.id)  # Convert to string for dictionary key
        await ctx.send('<a:time:1345383309458538518> Adding badge...')

        if user_id not in data_manager.badges:
            data_manager.badges[user_id] = set()
        data_manager.badges[user_id].add(badge)

        print(f'[DEBUG] Before save - badges: {data_manager.badges}')
        data_manager.save_data()
        print(f'[DEBUG] After save - badges: {data_manager.badges}')
        
        if data_manager.verify_data_consistency():
            await ctx.send(f'<:tick1:1389181551358509077> Successfully added {badge} badge to {user.name}!')
        else:
            await ctx.send('<a:nope1:1389178762020520109> Failed to save badge data consistently!')
    except Exception as e:
        print(f'[DEBUG] Error in givebadge: {str(e)}')
        await ctx.send(f'<a:nope1:1389178762020520109> An error occurred: {str(e)}')


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
            title='<:ticket1:1389284016099950693> Ticket Created',
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



@bot.command(name='mute')
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: int, *, reason=None):
    if member.top_role >= ctx.author.top_role:
        return await ctx.send('<a:nope1:1389178762020520109> You cannot mute someone with higher or equal role!')
    try:
        await member.timeout(discord.utils.utcnow() + datetime.timedelta(minutes=duration), reason=reason)
        embed = discord.Embed(
            title='<:tick1:1389181551358509077> Member Muted',
            description=f'{member.mention} has been muted <:mute1:1389605413132963951> for {duration} minutes\nReason: {reason or "No reason provided"}',
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send('<a:nope1:1389178762020520109> I cannot mute that member!')


# New Utility Commands



@bot.command(name='invites')
@commands.has_permissions(manage_guild=True)
async def invites(ctx):
    invites = await ctx.guild.invites()
    if not invites:
        return await ctx.send('<a:nope1:1389178762020520109> No invites found!')
    embed = discord.Embed(
        title=f'Invites for {ctx.guild.name}',
        color=discord.Color.blue()
    )
    for invite in invites:
        embed.add_field(
            name=f'<:rinvites:1345380642342572193> Invite by {invite.inviter}',
            value=f'Code: {invite.code}\nUses: {invite.uses}\nExpires: {invite.expires_at or "Never"}',
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command(name='lock')
@commands.has_permissions(manage_channels=True)
async def lock(ctx, channel: Optional[discord.TextChannel] = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(
        title='<:tick1:1389181551358509077> Channel Locked',
        description=f'{channel.mention} has been locked',
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command(name='unlock')
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, channel: Optional[discord.TextChannel] = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=True)
    embed = discord.Embed(
        title='<:tick1:1389181551358509077> Channel Unlocked',
        description=f'{channel.mention} has been unlocked',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# Run the bot
bot.run(TOKEN)
