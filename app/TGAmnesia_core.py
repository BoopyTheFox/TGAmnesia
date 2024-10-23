import argparse
#import getpass
import os
import time
import sys
import itertools
from dotenv import load_dotenv, set_key, unset_key
from telethon import TelegramClient, types, functions
from telethon.errors.rpcerrorlist import SessionPasswordNeededError
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, MessageMediaContact,
    MessageMediaGeo, MessageMediaVenue, MessageMediaGame, MessageMediaInvoice,
    MessageMediaWebPage, PeerUser, PeerChannel
)

load_dotenv('secrets_core.env')

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
PHONE_CODE_HASH = os.getenv('PHONE_CODE_HASH')

client = None


def save_secrets(api_id, api_hash, phone_number):
    set_key("secrets_core.env", "API_ID", api_id)
    set_key("secrets_core.env", "API_HASH", api_hash)
    set_key("secrets_core.env", "PHONE_NUMBER", phone_number)


async def auth(api_id, api_hash, phone_number):
    save_secrets(api_id=api_id, api_hash=api_hash, phone_number=phone_number)
    global client
    client = TelegramClient('tg_amnesia', api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        sent_code = await client.send_code_request(phone_number)
        phone_code_hash = sent_code.phone_code_hash

        # Saving to file to pass between sessions, for CLI-only use
        if os.path.exists("phone_code_hash.txt"):
            os.remove("phone_code_hash.txt")
        with open("phone_code_hash.txt", "w") as file:
            file.write(phone_code_hash)

        msg = "Now check your Telegram messages for 2FA code."
        print(msg)
        return msg


async def auth_2fa(code, password=None):
    global client
    if client is None:
        client = TelegramClient('tg_amnesia', API_ID, API_HASH)
        await client.connect()
    try:
        with open("phone_code_hash.txt", "r") as file:
            phone_code_hash = file.read().strip()
        await client.sign_in(PHONE_NUMBER, code, phone_code_hash=phone_code_hash)
        msg = "Telegram Amnesia authenticated and works\\nDO NOT FORGET TO TAP 'Yes, it is me!' BUTTON ON YOUR PHONE (it'll appear in a minute or so)\nIf you don't, your account might be FLAGGED AS COMPROMISED by Telegram, and you'll need to re-auth, but also link mail and all that stuff"
        await client.send_message('me', msg) 
        print(msg)
        # Remove the file after successful authentication
        os.remove("phone_code_hash.txt")
        return msg
    except SessionPasswordNeededError:
        if password is None:
            #password = getpass.getpass(prompt="Two-step verification is enabled. Please enter your password: ")
            msg = "Cloud password is set for this device. Please provide password after code as well."
            print(msg)
            return msg
        else:
            await client.sign_in(password=password)
            msg = "Telegram Amnesia authenticated and works\n\nDO NOT FORGET TO TAP 'Yes, it is me!' BUTTON ON YOUR PHONE (it'll appear in a few seconds)"
            await client.send_message('me', msg)
            print(msg)
            return msg
    except Exception as e:
        msg = f"Error during authentication: {str(e)}"
        print(msg)
        return msg


async def deauth():
    global client
    if client is None:
        client = TelegramClient('tg_amnesia', API_ID, API_HASH)
        await client.connect() 
    await client.log_out()
    await client.disconnect()
    
    if os.path.exists('secrets_core.env'):
        os.remove('secrets_core.env')
   
    msg = "Deauthenticated successfully!"
    print(msg)
    return msg


async def ping():
    global client
    if client is None:
        client = TelegramClient('tg_amnesia', API_ID, API_HASH)
        await client.start()
    result = await client(functions.help.GetNearestDcRequest())
    msg = f"Pong! Nearest DC: {result.nearest_dc}, This DC: {result.this_dc}"
    print(msg)
    return msg


async def group_list():
    global client
    if client is None:
        client = TelegramClient('tg_amnesia', API_ID, API_HASH)
        await client.start()

    group_list = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            group_name = f"{dialog.id}\t{dialog.name}"
            print(group_name)
            group_list.append(group_name)
    
    return group_list


async def group_show(group_partial_name):
    global client
    if client is None:
        client = TelegramClient('tg_amnesia', API_ID, API_HASH)
        await client.start()

    msg = ""
    groups = []
    async for dialog in client.iter_dialogs():
        if group_partial_name.lower() in dialog.name.lower():
            groups.append(dialog)

    if not groups:
        msg += f"No groups matching '{group_partial_name}' found.\n"
        print(msg)
        return msg

    for dialog in groups:
        entity = await client.get_entity(dialog)
        user_id = (await client.get_me()).id
        total_messages = await client.get_messages(entity, limit=0)
        total_system_messages = await client.get_messages(entity, from_user='me', limit=0)
        
        msg += f"Group ID: {dialog.id}\n"
        msg += f"Group Name: {dialog.name}\n"
        msg += f"Total messages: {total_messages.total}\n"
        
        user_messages = []
        system_messages = []
        async for message in client.iter_messages(entity, from_user=user_id):
            if message.action is None:  # Check if message has no action
                user_messages.append(message)
            else:
                system_messages.append(message)
        
        msg += f"Messages from you: {len(user_messages)}\n"
        if user_messages:
            msg += f"Oldest user message date: {user_messages[-1].date.strftime('%Y-%m-%d %H:%M')}\n"
        
        msg += f"System messages linked to you: {len(system_messages)}\n"
        if system_messages:
            msg += f"Oldest system message date: {system_messages[-1].date.strftime('%Y-%m-%d %H:%M')}\n"
        msg += "\n" # To separate the messages, if there are many groups

    print(msg)
    return msg


#async def group_show_reactions(group_partial_name, batch_size=100, quiet=False):
#    global client
#    if client is None:
#        client = TelegramClient('tg_amnesia', API_ID, API_HASH)
#        await client.start()
#
#    groups = []
#    async for dialog in client.iter_dialogs():
#        if group_partial_name.lower() in dialog.name.lower():
#            groups.append(dialog)
#
#    if not groups:
#        print(f"No groups matching '{group_partial_name}' found.")
#        return
#
#    for dialog in groups:
#        entity = await client.get_entity(dialog)
#        user_id = (await client.get_me()).id
#        total_messages = await client.get_messages(entity, limit=0)
#        if not quiet:
#            print(f"Group ID: {dialog.id}")
#            print(f"Group Name: {dialog.name}")
#            print(f"Total messages: {total_messages.total}")
#
#        reactions_from_you = 0  # Counter for reactions from you
#        processed_messages = 0  # Counter for processed messages
#        async for message in client.iter_messages(entity, from_user=user_id):
#            processed_messages += 1
#            if processed_messages % batch_size == 0 and not quiet:
#                sys.stdout.write(f"\rProcessed {processed_messages} messages...")
#                sys.stdout.flush()
#            if message.reactions and message.reactions.recent_reactions:
#                for reaction in message.reactions.recent_reactions:
#                    if isinstance(reaction.peer_id, PeerUser) and reaction.peer_id.user_id == user_id:
#                        reactions_from_you += 1
#        
#        if not quiet:
#            print(f"\rProcessed {processed_messages} messages... Done!")
#            print(f"Reactions from you: {reactions_from_you}")


async def group_purge(group_partial_name, message_pattern=None, quiet=False):
    global client
    if client is None:
        client = TelegramClient('tg_amnesia', API_ID, API_HASH)
        await client.start()

    msg = ""
    groups = []
    async for dialog in client.iter_dialogs():
        if group_partial_name.lower() in dialog.name.lower():
            groups.append(dialog)

    if not groups:
        msg += f"No groups matching '{group_partial_name}' found."
        print(msg)
        return msg

    for dialog in groups:
        entity = await client.get_entity(dialog)
        user_id = (await client.get_me()).id

        print(f"Started purging messages from group: {dialog.id} - {dialog.name}")
        spinner = itertools.cycle(['|', '/', '-', '\\'])
        async for message in client.iter_messages(entity, from_user=user_id):
            # If message_pattern is provided, skip messages that not match it
            if message_pattern and not re.search(message_pattern, message.text or ''):
                continue

            await client.delete_messages(entity, message)
            if not quiet:
                sys.stdout.write(next(spinner))  # write the next character
                sys.stdout.flush()               # flush stdout buffer (actual character display)
                sys.stdout.write('\b')           # erase the last written char

        msg += f"Successfully purged messages from group: {dialog.id} - {dialog.name}\n"
        print(f"Successfully purged messages from group: {dialog.id} - {dialog.name}")
    
    return msg
async def group_dump(group_partial_name, send=False):
    global client
    if client is None:
        client = TelegramClient('tg_amnesia', API_ID, API_HASH)
        await client.start()
    
    print(f"Started dumping messages...")
    
    groups = []
    async for dialog in client.iter_dialogs():
        if group_partial_name.lower() in dialog.name.lower():
            groups.append(dialog)

    if not groups:
        msg = f"No groups matching '{group_partial_name}' found."
        print(f"No groups matching '{group_partial_name}' found.")
        return msg

    media_types = {
        MessageMediaPhoto: "[PHOTO]",
        MessageMediaDocument: "[DOCUMENT]",
        MessageMediaContact: "[CONTACT]",
        MessageMediaGeo: "[GEO]",
        MessageMediaVenue: "[VENUE]",
        MessageMediaGame: "[GAME]",
        MessageMediaInvoice: "[INVOICE]",
        MessageMediaWebPage: "[WEBPAGE]",
    }

    service_types = {
        types.MessageActionChannelCreate: "[CHANNEL CREATE]",
        types.MessageActionChannelMigrateFrom: "[CHANNEL MIGRATE FROM]",
        types.MessageActionChatAddUser: "[CHAT ADD USER]",
        types.MessageActionChatCreate: "[CHAT CREATE]",
        types.MessageActionChatDeletePhoto: "[CHAT DELETE PHOTO]",
        types.MessageActionChatDeleteUser: "[CHAT DELETE USER]",
        types.MessageActionChatEditPhoto: "[CHAT EDIT PHOTO]",
        types.MessageActionChatEditTitle: "[CHAT EDIT TITLE]",
        types.MessageActionChatJoinedByLink: "[CHAT JOINED BY LINK]",
        types.MessageActionChatMigrateTo: "[CHAT MIGRATE TO]",
        types.MessageActionContactSignUp: "[CONTACT SIGN UP]",
        types.MessageActionCustomAction: "[CUSTOM ACTION]",
        types.MessageActionEmpty: "[EMPTY]",
        types.MessageActionGameScore: "[GAME SCORE]",
        types.MessageActionHistoryClear: "[HISTORY CLEAR]",
        types.MessageActionPaymentSent: "[PAYMENT SENT]",
        types.MessageActionPaymentSentMe: "[PAYMENT SENT ME]",
        types.MessageActionPhoneCall: "[PHONE CALL]",
        types.MessageActionPinMessage: "[PIN MESSAGE]",
        types.MessageActionScreenshotTaken: "[SCREENSHOT TAKEN]",
        types.MessageActionSecureValuesSent: "[SECURE VALUES SENT]",
        types.MessageActionSecureValuesSentMe: "[SECURE VALUES SENT ME]",
    }

    for dialog in groups:
        entity = await client.get_entity(dialog)
        user_id = (await client.get_me()).id
        messages = []
        async for message in client.iter_messages(entity, from_user=user_id):
            messages.append(message)

        msg = ""
        filename = f"{dialog.name}_dump.txt"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(f"Group ID: {dialog.id}\n")
            file.write(f"Group Name: {dialog.name}\n")
            file.write("\n")
            for message in messages:
                file.write(f"ID {message.id} {message.date.strftime('%Y-%m-%d %H:%M:%S')}\n")
                if message.text:
                    file.write(f"Content: {message.text}\n")
                elif message.media:
                    media_class = type(message.media)
                    media_type = media_types.get(media_class, "[MEDIA]")
                    # Enhanced media type detection for specific document types
                    if media_class is MessageMediaDocument:
                        for attr in message.media.document.attributes:
                            if isinstance(attr, types.DocumentAttributeSticker):
                                media_type = f"[STICKER - {attr.alt}]"
                            elif isinstance(attr, types.DocumentAttributeAudio):
                                if attr.voice:
                                    media_type = f"[VOICE MSG - {attr.duration // 60}:{attr.duration % 60:02}]"
                                else:
                                    media_type = f"[AUDIO - {attr.duration // 60}:{attr.duration % 60:02}]"
                            elif isinstance(attr, types.DocumentAttributeAudio) and attr.voice:
                                media_type = f"[VOICE MSG - {attr.duration // 60}:{attr.duration % 60:02}]"
                            elif isinstance(attr, types.DocumentAttributeVideo):
                                media_type = f"[VIDEO MSG - {attr.duration} seconds]"
                    file.write(f"Content: {media_type}\n")
                elif isinstance(message.action, tuple(service_types.keys())):
                    service_type = service_types[type(message.action)]
                    file.write(f"Content: {service_type}\n")
                else:
                    file.write("Content: [OTHER]\n")
                file.write("\n")

        if send:
            await client.send_file('me', filename, caption=f"Dump of group {dialog.name}")
            os.remove(filename)
            msg += f"Dump sent to your Saved Messages"
            print(f"Dump sent to your Saved Messages")
            return msg
        else:
            msg += f"Dump saved to {filename}"
            print(f"Dump saved to {filename}")
            return msg


async def main():
    parser = argparse.ArgumentParser(description="TGAmnesia Core Script")
    parser.add_argument('--auth', nargs=3, metavar=('API_ID', 'API_HASH', 'PHONE_NUMBER'), help='Authenticate')
    parser.add_argument('--auth-2fa', nargs='+', metavar='CODE', help='Complete authentication with 2FA code and password')
    parser.add_argument('--deauth', action='store_true', help='Deauthenticate')
    parser.add_argument('--ping', action='store_true', help='Ping Telegram API')
    parser.add_argument('--group-list', action='store_true', help='List your groups')
    parser.add_argument('--group-show', metavar='GROUP_NAME', help='Show specified group(s) information')
    #parser.add_argument('--group-show-reactions', type=str, help='Show group reactions information for given partial group name')
    parser.add_argument('--group-dump', metavar='GROUP_NAME', help='Dump specified group(s) messages into a file, or [--send] to telegram')
    parser.add_argument('--send', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--group-purge', metavar='GROUP_NAME', help='Purge specified group(s) messages')
    parser.add_argument('--quiet', action='store_true', help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.auth:
        api_id, api_hash, phone_number = args.auth
        await auth(api_id, api_hash, phone_number)
        return
    elif args.auth_2fa:
        if len(args.auth_2fa) == 1:
            await auth_2fa(args.auth_2fa[0])
            return
        else:
            await auth_2fa(args.auth_2fa[0], password=args.auth_2fa[1])
            return
    elif args.deauth:
        await deauth()
        return
    elif args.ping:
        await ping()
        return
    elif args.group_list:
        await group_list()
        return
    elif args.group_show:
        await group_show(args.group_show)
        return
    #elif args.group_show_reactions:
    #    await group_show_reactions(args.group_show_reactions, quiet=args.quiet)
    #    return
    elif args.group_dump:
        await group_dump(args.group_dump, send=args.send)
        return
    elif args.group_purge:
        await group_purge(args.group_purge, args.quiet)
        return
    else:
        return

    if not API_ID or not API_HASH or not PHONE_NUMBER:
        print("User not found, do `--auth [api_id] [api_hash] [phone_number]`")
        return

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
