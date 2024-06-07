# Telegram Amnesia

**TGAmnesia** is a simple tool to bulk-remove your own messages from select telegram groups.

It can be used either on it's own, or through telegram bot as a wrapper. It is also dockerized.

## Dependencies
Either just have **docker**, or:

Required -
- Python
- Telethon - to interact with Telegram Client API (Also referred to as "MTProto API")
- python-dotenv - to store authentication data

Optional (if you want to automate it within regular intervals) -
- Cron service (tested on Debian's "cron" and Arch's "cronie")
- python-crontab

## How to use

### Create your "app"
Here's the [official instruction](https://core.telegram.org/api/obtaining_api_id)

Here's the short version:
1. Go to my.telegram.org
2. Auth with your phone number
3. Go to "API management tool" and fill out necessary fields 
4. Obtain your secrets - copy **api_id**, **api_hash**, and store them securely.

### (If needed) Create your "bot"
Here's the [official instruction](https://core.telegram.org/bots/tutorial) ("Getting Ready" section)

Here's the short version:
1. In telegram client, go to @BotFather
2. Enter command **/newbot** and follow intructions
3. You'll get a **BOT_TOKEN** that'd look something like this - `1234567890:ABCD1E2EFgHI3jPMC7k6lfsD33ZNuTZhHTrlA`. Save it with all other secrets.

### Option 1 - Use script from CLI

1. Clone the repo:
```bash
git clone https://github.com/BoopyTheFox/TGAmnesia/
cd TGAmnesia/app
```

2. Create python virtual environment and install dependencies in it:
```bash
mkdir venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Go through authentication - put in secrets, obtained earlier, and then 2fa code + your tg password, if set.

*(tip: if you don't want your secrets to save in shell history, put a space in beginning of your command!)*
```bash
python3 TGAmnesia_core.py --auth $api_id $api_hash $your_phone_number
python3 TGAmnesia_core.py --auth-2fa $auth_code $password
```

Now you can use it!

List your groups:
```bash
python3 TGAmnesia_core.py --group-list
```

Show info about some group(s), matching by name:
```bash
python3 TGAmnesia_core.py --group-show $part_of_a_group_name
```

Purge your messages from a group:
```bash
python3 TGAmnesia_core.py --group-purge $part_of_a_group_name
```

You can also dump your messages from a group if you want to review it:

*(note - any non-text message will show as [TAG], depending on it's type)*
```bash
python3 TGAmnesia_core.py --group-dump $part_of_a_group_name
```

If you just wanted to remove your messages once, don't forget to deauth and remove your secrets:
```bash
python3 TGAmnesia_core.py --deauth
cd ../../
rm -r TGAmnesia
```

You can also schedule tasks using `TGAmnesia_schedule.py`:

Schedule periodic purging:
*(note: you can use m for minutes, h for hours, d for days)*
```bash
python3 TGAmnesia_schedule.py --schedule-purge $part_of_a_group_name 30m
```

Show currently scheduled jobs:
```bash
python3 TGAmnesia_schedule.py --list-jobs $part_of_a_group_name
```

Remove one or several scheduled jobs:
```bash
python3 TGAmnesia_schedule.py --rm-job $part_of_a_group_name
```

### Option 2 - Use it through Telegram Bot
You can use telegram bot as a wrapper:

#### 1. Initialize your bot
First 3 steps are same as above, in "Option 1 - Use script from CLI".

Then do this:

*(note: enter your username without @)*
```bash
python3 TGAmnesia_bot.py --init $your_user_name $api_id $api_hash $bot_token
```

#### 2. Use your bot
In your telegram bot:
On /start, you'll get authentication instructions.
On /help, you can read them again, and see all other commands.

### Option 3 - Telegram Bot in Docker container
1. Clone the repo - `git clone https://github.com/BoopyTheFox/TGAmnesia/ && cd TGAmnesia`
2. Deploy your container - `./init.sh $your_user_name $api_id $api_hash $bot_token`
3. Go to the bot, auth in the bot

## IMPORTANT NOTE (how to not lose your account)
As of May 2024, telegram support leaves NO FEEDBACK AT ALL (even though they do review and resolve user's tickets), so don't get discouraged if you won't receive any.

As telegram [officially states](https://core.telegram.org/api/obtaining_api_id) (at least on May 2024):
> Due to excessive abuse of the Telegram API, **all accounts** that sign up or log in using unofficial Telegram API clients are automatically put **under observation** to avoid violations of the [Terms of Service](https://core.telegram.org/api/terms)

Also, telegram anti-fraud is heavily automated (as it should be), and unless you do some precautions, it **will** do the following things:
- **Force de-auth** your account from all sessions
- Force you to link / re-link an e-mail to it (you can change back to your main one later)
- Will throw PHONE_CODE_EXPIRED and EMAIL_NOT_ALLOWED and laugh at you

### What can trigger it
- Flagged IP's (Most **VPN**s)
- Being in different locations at the same time
- Incomplete login attempts
- Not tapping "Yes, it was me!" in mobile client seconds after you logged in
- Probably something else i don't know

### How to avoid it
- **Tap that "Yes, it was me!"** button in your mobile client after you authenticate. It shows up to a minute late
- If you use VPN, whitelist [these](https://core.telegram.org/resources/cidr.txt)
- If you can't whitelist, and your VPN comes out of another country, don't use VPN when logging in

## Other notes
- 2FA code **in Telegram Bot** needs to be entered **in reverse** - that's because telegram detects if your 2FA code have been shared through your telegram account, blocking login attempt.
- Telegram seems to be indexing messages within irregular intervals, about ~5-10 minutes. So, even if you schedule purge every minute, fresh messages will be purged some time later. 
- If your docker container seems to be stuck on installing dependencies - it's a DNS issue. Turn off your VPN tun, or set up docker network through it.
