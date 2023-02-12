#!/usr/bin/env bash

if [ -z "$*" ]; then
    echo -e "\033[0;31mTOKEN must be provided\033[0m"
    exit 1
fi

docker pull kruase/codenames_bot
docker run -dti \
    --name codenames_bot \
    -e TOKEN="$1" \
    -v codenames_bot_state:/bot/state \
    kruase/codenames_bot
