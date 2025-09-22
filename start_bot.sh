#!/bin/sh

printf %80s |tr " " "="
printf "\n"

python --version
pip --version

echo "Update EveEchoes Telegram Bot database version"
python -m utils.migrations apply

echo "Launching the EveEchoes Telegram Bot"
python eetgbot.py
