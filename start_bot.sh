#!/bin/sh

printf %80s |tr " " "="
printf "\n"
python --version
pip --version
printf %80s |tr " " "="
printf "\n"

echo "Launching the EveEchoes Telegram Bot"
python launcher.py -v DEBUG
