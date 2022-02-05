
# VegiBoxBot

This application is an example on how one could set up a web scraping telegram bot in Python
to keep a user base up-to-date about the scraped products. 

I run a version of this bot on heroku to keep users up-to-date about their abos at a local vegetable delivery service. 
As this user base is mainly german speaking, the messages set here to send to the users are all in german language.

## Features

The users can:
- set a favorite abo by walking through an inline button guided questionnaire
- set a weekly reminder for their favorite and specify weekday, hour and minute of the reminder
- ask for the abos' ingredients of the current or the next calendar week
- ask for another abos' ingredients of the current or next calendar week by passing arguments
- ask for all abos available
- ask for the currently set favorite
- ask for the currently set reminder
- delete  favorite
- delete currently set reminder

<img src="./media/example.gif" height="300">

## Prerequisites

1. To use the tool, generally make sure
   1. you created a telegram bot with [Telegrams BotFather](https://telegram.me/botfather) and have got a valid
   Bot token for it.
      1. As you can see in the TBot class in TBotEngine, it's even recommended, to set up a second bot for testing
      purposes.
   2. you installed all the modules from the [requirements.txt](requirements.txt) 
   and potential dependencies.
2. To run the tool on heroku, make sure 
   1. you created an account and followed the tutorial on how to deploy a python
   application.
   2. you added the AddON Heroku Postgres to your app and got the url of the database.
   3. you set following environment variables in heroku:
      1. IS_HEROKU (the value doesn't matter though)
      2. APP_NAME = \<Your app name in heroku>
      3. DATABASE_URL = \<the database url of your heroku PostgreSQL>
      4. TELEGRAM_BOT_TOKEN = \<the token of your main bot>
   4. you correctly set up a Procfile as mentioned in the tutorials
3. To run the tool locally, make sure
   1. you created a file "Credentials.env" and added following environment keys:
      1. TELEGRAM_BOT_TOKEN
      2. TELEGRAM_BOT_DEV_TOKEN = \<bot token of the bot for local testing purposes>
      3. APP_NAME
      4. HEROKU_API_KEY = \<your heroku api>
4. Change all set variables in [SqlConnector.py](SqlConnector.py), [TBotEngine.py](TBotEngine.py) and edit everything
else according to your needs!

## Known Issues
For a few years now the free version of heroku needs applications to sleep at least for 6 hours within 24 hours.
Also, heroku hibernates applications after approx. 30 minutes of no incoming https-requests. For the second issue the
service of [kaffeine](https://kaffeine.herokuapp.com/) is a valid workaround. As there is no workaround for the 
first issue, reminders can only be set within hours the application is up.

## License

[MIT](https://choosealicense.com/licenses/mit/)

MIT License

Copyright (c) [2022] [Simon Schwarzkopf]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

