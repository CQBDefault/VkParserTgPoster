# As first
Install the dependencies:
```python install -r requirements.txt```

# Settings
`last_id` — put the last post ID from wall

`login` — input login from your (or not your :D) VK account

`password` — input password

`domain` — input namelink of public or user


Example:
```
domain = cqb.default
```
`count` — count of post they will be parsed

`token` — will be filled automatically

`bot_token` — input token of your Telegram bot

`channel` — input name of your channel, with @

# WARNING
If in post there are several images, bot will send text in first post, images — in second.
The bot works very poorly with reposts, everything will be sent in turn.
