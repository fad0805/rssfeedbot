# Misskey RSS bot
## INSTALL
`poetry install`

## Set cron
`0 * * * * cd rssfeedbot/ && /usr/bin/python3 -m poetry run python main.py >> rssfeedbot/cron.log 2>&1`
