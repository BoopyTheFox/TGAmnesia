#!/bin/bash

display_help() {
  echo "Usage: $0 <user_name> <api_id> <api_hash> <bot_token>"
  exit 0
}

if [[ $1 == "-h" || $1 == "--help" ]]; then
  display_help
fi

if ! docker ps > /dev/null 2>&1; then
  echo "Insufficient privileges to run Docker. Please add your user to the docker group or run as root."
  exit 1
fi

if [ "$(docker ps -a | grep tgamnesia)" ]; then
  echo "TGAmnesia container already exists. Exiting."
  exit 1
fi

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 <user_name> <api_id> <api_hash> <bot_token>"
  exit 1
fi

USER_NAME=$1
API_ID=$2
API_HASH=$3
BOT_TOKEN=$4

cat <<EOF > ./app/secrets_bot.env
USER_NAME=$USER_NAME
API_ID=$API_ID
API_HASH=$API_HASH
BOT_TOKEN=$BOT_TOKEN
EOF

docker build -t tgamnesia . && docker run -d --name tgamnesia tgamnesia

if [ $? -eq 0 ]; then
  echo "TGAmnesia container is now running."
else
  echo "Failed to start TGAmnesia container."
fi

rm ./app/secrets_bot.env
