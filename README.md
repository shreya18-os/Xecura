# Xecura Discord Bot

A multipurpose Discord bot with custom badges, profile system, and no-prefix functionality.

## Features

- Custom prefix system (`x!`)
- Profile command with custom badges
- No-prefix mode for privileged users
- Interactive help menu with dropdown categories
- Badge management system
- Custom emoji support throughout all commands

## Commands

### General
- `x!help` - Shows the interactive help menu
- `x!ping` - Displays bot's latency

### Profile
- `x!profile [user]` - Shows user profile with badges

### Admin (Owner Only)
- `x!givebadge <user> <badge>` - Gives a badge to a user
- `x!removebadge <user> <badge>` - Removes a badge from a user
- `x!togglenoprefix <user>` - Toggles no-prefix mode for a user

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables in Railway:
   - `BOT_TOKEN` - Your Discord bot token

4. Replace the emoji IDs in the code with your custom emoji IDs

## Badge Types

- Owner Badge
- Admin Badge
- Staff Badge
- No-Prefix Badge
- No Badge (default)

## No-Prefix System

Users with no-prefix privileges can use commands without the `x!` prefix. This feature can only be toggled by the bot owner.

## Data Storage

User data (badges and no-prefix status) is stored locally in `data.json` and is automatically managed by the bot.

## Note

Make sure to replace all emoji placeholders (`<emoji:ID>`) with your actual custom emoji IDs before running the bot.