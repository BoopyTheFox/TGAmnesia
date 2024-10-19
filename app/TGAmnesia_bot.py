import sys
import argparse
import os
from telethon import TelegramClient, events, sync
import TGAmnesia_core
import TGAmnesia_scheduler

parser = argparse.ArgumentParser(description="Telegram Bot Setup with CLI initialization")
parser.add_argument("--init", 
                    nargs=4, 
                    help="Initialize bot settings <user_name> <api_id> <api_hash> <bot_token>", 
                    metavar=("USER_NAME", "API_ID", "API_HASH", "BOT_TOKEN")
                    )
args = parser.parse_args()

if args.init:
    user_name, api_id, api_hash, bot_token = args.init
    with open("secrets_bot.env", "w") as file:
        file.write(f"USER_NAME={user_name}\nAPI_ID={api_id}\nAPI_HASH={api_hash}\nBOT_TOKEN={bot_token}\n")
    print("Bot initiated!")
else:
    from dotenv import load_dotenv
    load_dotenv("secrets_bot.env")
    user_name = os.getenv("USER_NAME")
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    bot_token = os.getenv("BOT_TOKEN")

if not all([api_id, api_hash, bot_token]):
    print("Please initialize bot with --init <your_user_name> <api_id> <api_hash> <bot_token>") 
    sys.exit(1)

allowed_usernames = [user_name]

bot = TelegramClient('tg_amnesia_bot', int(api_id), api_hash).start(bot_token=bot_token)


async def run_and_return(event, func, *args):
    if event.sender.username in allowed_usernames:
        result = await func(*args)
        if result:
            await event.respond(result)
        else:
            await event.respond("/help")
    else:
        await event.respond("You're not allowed to use this command.")


@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    start_text = """
Welcome! 
To authenticate: 
Step 1 - /auth <api_id> <api_hash> <phone_number>
Step 2 - /auth_2fa <2fa-code> <password>

NOTE:
* Enter <2fa-code> IN REVERSE ORDER, to prevent Telegram from blocking login attempt.
* If <password> is not set, you don't have to enter it
* Also, remember to delete messages containing your data.
"""
    await event.respond(start_text)


@bot.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    help_text = """
--- Available commands ---
/help - Show this help message

Authentication:
/auth <api_id> <api_hash> <phone_number> - Authenticate
/auth_2fa <2fa-code_reversed> <password> - Authenticate with 2FA
/deauth - Deauthenticate

Usage:
/ping - Check Telegram API status
/group_list - Get group list
/group_show <group_name> - Show group(s) info
/group_purge <group_name> - Purge group(s) messages
/group_dump <group_name> - Dump group(s) messages

Scheduling:
/schedule <group_name> <time_interval> - Schedule a purge for specified group(s)
/unschedule <group_name> - Remove a scheduled purge
/schedules - List scheduled purges
"""
    await event.respond(help_text)


@bot.on(events.NewMessage(pattern='/ping'))
async def ping_command(event):
    await event.respond("Pinging...")
    await run_and_return(event, TGAmnesia_core.ping)


@bot.on(events.NewMessage(pattern='/auth( .+)?'))
async def auth_command(event):
    if event.pattern_match.group(1) is None:
        await event.respond("Usage: /auth <api_id> <api_hash> <phone_number>")
    else:
        await event.respond("Authenticating...")
        api_id, api_hash, phone_number = event.pattern_match.group(1).strip().split()
        await run_and_return(event, TGAmnesia_core.auth, api_id, api_hash, phone_number)


@bot.on(events.NewMessage(pattern='/auth_2fa( .+)?'))
async def auth_2fa_command(event):
    if event.pattern_match.group(1) is None:
        await event.respond("Usage: /auth_2fa <2fa-code_reversed> <password>")
    else:
        await event.respond("2FA-ing...")
        args = event.pattern_match.group(1).strip().split()
        reversed_code = args[0]
        code = reversed_code[::-1]
        password = args[1] if len(args) > 1 else None
        await run_and_return(event, TGAmnesia_core.auth_2fa, code, password)


@bot.on(events.NewMessage(pattern='/deauth'))
async def deauth_command(event):
    await event.respond("Deauthenticating...")
    await run_and_return(event, TGAmnesia_core.deauth)


@bot.on(events.NewMessage(pattern='/group_list'))
async def group_list_command(event):
    await event.respond("Getting group list...")
    await run_and_return(event, TGAmnesia_core.group_list)


@bot.on(events.NewMessage(pattern='/group_show( .+)?'))
async def group_show_command(event):
    if event.pattern_match.group(1) is None:
        await event.respond("Usage: /group_show <group_name>")
    else:
        await event.respond("Getting info about groups...")
        group_partial_name = event.pattern_match.group(1).strip()
        await run_and_return(event, TGAmnesia_core.group_show, group_partial_name)


@bot.on(events.NewMessage(pattern='/group_purge( .+)?'))
async def group_purge_command(event):
    if event.pattern_match.group(1) is None:
        await event.respond("Usage: /group_purge <group_name> [message_pattern]")
    else:
        await event.respond("Purging messages...")
        args = event.pattern_match.group(1).strip().split(' ', 1)
        group_partial_name = args[0]
        message_pattern = args[1] if len(args) > 1 else None
        await run_and_return(event, TGAmnesia_core.group_purge, group_partial_name, message_pattern)


@bot.on(events.NewMessage(pattern='/group_dump( .+)?'))
async def group_dump_command(event):
    if event.pattern_match.group(1) is None:
        await event.respond("Usage: /group_dump <group_name>")
    else:
        await event.respond("Dumping messages...")
        group_partial_name = event.pattern_match.group(1).strip()
        await run_and_return(event, TGAmnesia_core.group_dump, group_partial_name, True)


@bot.on(events.NewMessage(pattern='/schedule( .+)?'))
async def schedule_purge_command(event):
    if event.pattern_match.group(1) is None:
        await event.respond("Usage: /schedule <group_name> <time_interval>")
    else:
        await event.respond("Scheduling purge...")
        args = event.pattern_match.group(1).strip().split()
        if len(args) < 2:
            await event.respond("Usage: /schedule <group_name> <time_interval>")
        else:
            group_name, time_interval = args
            await run_and_return(event, TGAmnesia_scheduler.schedule_purge, group_name, time_interval)


@bot.on(events.NewMessage(pattern='/schedules'))
async def list_schedules_command(event):
    await event.respond("Getting schedule list...")
    await run_and_return(event, TGAmnesia_scheduler.list_jobs)


@bot.on(events.NewMessage(pattern='/unschedule( .+)?'))
async def unschedule_purge_command(event):
    if event.pattern_match.group(1) is None:
        await event.respond("Usage: /unschedule <group_name>")
    else:
        await event.respond("Removing a scheduled purge...")
        group_name = event.pattern_match.group(1).strip()
        await run_and_return(event, TGAmnesia_scheduler.remove_job, group_name)


if not args.init:
    print("Bot is running...")
    bot.run_until_disconnected()

