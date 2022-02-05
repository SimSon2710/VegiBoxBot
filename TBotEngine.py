import typing
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackContext, CommandHandler, CallbackQueryHandler
from dataclasses import dataclass
from os import environ
from AboBox import AboBox
from UserFavorite import UserFavorite
from User import User
from Reminder import Reminder
from collections import OrderedDict
from datetime import time
from pytz import timezone
from time import sleep
import logging

@dataclass
class TBot:
    logger = logging.getLogger(__name__)

    on_heroku = False
    if "IS_HEROKU" in environ:
        on_heroku = True
    if on_heroku:
        TOKEN = environ.get("TELEGRAM_BOT_TOKEN")
        NAME = environ.get("APP_NAME")
        PORT = environ.get('PORT')
    else:
        from dotenv import dotenv_values
        print("running in dev environment: https://telegram.me/<YOUR BOT NAME>")
        TOKEN = dotenv_values(r'Credentials.env')['TELEGRAM_BOT_DEV_TOKEN']
        NAME = dotenv_values(r'Credentials.env')["APP_NAME"]
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    handlers = []

    def __init__(self) -> None:
        super().__init__()
        self.add_handlers()

    def add_handlers(self):
        handlers = [
            CommandHandler('start', self.message_start, pass_args=False),
            CommandHandler('diese_woche', self.message_get_abo_details_cur_week, pass_args=True),
            CommandHandler('naechste_woche', self.message_get_abo_details_next_week, pass_args=True),
            CommandHandler('alle_abos', self.message_get_all_box_names, pass_args=False),
            CommandHandler('help', self.message_help, pass_args=False),
            CommandHandler('set_favorit', self.message_set_abo_fave, pass_args=False),
            CommandHandler('mein_favorit', self.message_get_abo_fave, pass_args=False),
            CommandHandler('bot_loeschen', self.message_remove_user, pass_args=False),
            CommandHandler('erinnere_mich', self.message_set_reminder),
            CommandHandler('meine_erinnerung', self.message_get_reminder, pass_args=False),
            CommandHandler('erinnerung_loeschen', self.message_remove_reminder, pass_args=False),
            CallbackQueryHandler(self.button_pressed)
        ]
        for handler in handlers:
            self.dispatcher.add_handler(handler=handler)

    def start_bot(self):
        if self.on_heroku:
            self.updater.start_webhook(listen="0.0.0.0",
                                       port=int(self.PORT),
                                       url_path=self.TOKEN,
                                       webhook_url=f"https://{self.NAME}.herokuapp.com/{self.TOKEN}")
        else:
            self.updater.start_polling()

    # helper method to define the inline button markup for choosing abo favorites after
    # user called /set_favorit or /start
    @classmethod
    def set_markup_abo_fave(cls):
        subscriptions = cls.get_all_boxes_sorted()
        subscription_title_buttons = []
        lines = []
        for i, (key, subs) in enumerate(subscriptions.items()):
            lines.append(InlineKeyboardButton(key, callback_data=key))
            if i % 2 == 0:
                subscription_title_buttons.append(lines)
                lines = []
        subscription_title_buttons.append([InlineKeyboardButton("❌", callback_data='reject')])
        return InlineKeyboardMarkup(subscription_title_buttons)

    # helper method which checks, whether keywords (abo name and size) were defined and if not, it checks if the user
    # has already set up a favorit...else it returns an error/help-text
    @classmethod
    def get_abo_details(cls, chat_id: str, context_args: list, week: str) -> typing.Union[tuple, str]:
        fave = UserFavorite.get_from_chat_id(chat_id=str(chat_id))
        if context_args:
            box_name = context_args[0]
            try:
                box_size = context_args[1]
            except IndexError:
                box_size = ''
        elif fave:
            box_name = fave.box_name.lower()
            box_size = fave.box_size.lower()
        else:
            return f"Du hast noch keinen Favoriten festgelegt. Lege einen Favoriten über /set_favorit fest.\n" \
                   f"Alternativ kannst du auch direkt nach Abos suche durch z. B. <i>/{week} mix mittel</i>."

        return box_name, box_size

    # helper method which, first, clusters the abo boxes, second, sort the clustered boxes, third, sort the boxes within
    # the clusters and last, returns a dict of clustered and sorted boxes
    @classmethod
    def get_all_boxes_sorted(cls) -> dict:
        boxes_dic = {}
        for box in AboBox.boxes_lst:
            try:
                boxes_dic[box.name.split()[0]].append(box.name)
            except KeyError:
                boxes_dic[box.name.split()[0]] = [box.name]
        boxes_dic = OrderedDict(sorted(boxes_dic.items()))
        for lsts in boxes_dic:
            boxes_dic[lsts] = list(set(boxes_dic[lsts]))
        return boxes_dic

    # adds the stored reminders to the app scheduler
    def load_reminders(self):
        reminders = Reminder.load_from_db()
        for reminder in reminders:
            CallbackContext(self.dispatcher).job_queue.run_daily(
                self.send_reminder_message,
                # specify your timezone!
                time=time(hour=reminder.hour, minute=reminder.minute, tzinfo=timezone('Europe/Berlin')),
                days=([reminder.day_of_week]),
                context=reminder.chat_id,
                name=reminder.chat_id
            )

    # handles the behavior if a user pressed inline buttons
    def button_pressed(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()
        subscriptions = self.get_all_boxes_sorted()
        chat_data = context.chat_data
        if query.data == "reject":
            query.delete_message()
        elif query.data in subscriptions.keys():
            context.chat_data['fave_first'] = query.data
            sub_menu_markup = [[InlineKeyboardButton(s, callback_data=s)] for s in subscriptions[query.data]]
            sub_menu_markup.append([InlineKeyboardButton("❌", callback_data='reject')])
            query.edit_message_text(
                text="Wähle nun deinen Favoriten aus:",
                reply_markup=InlineKeyboardMarkup(sub_menu_markup)
            )
        elif 'fave_first' in chat_data:
            query.edit_message_text(text=f"Dein neuer Favorit ist nun: \"{query.data}\"")
            chat_data.clear()
            UserFavorite.set_from_query(chat_id=str(update.effective_chat.id), box_name=query.data, box_size='')
        elif query.data == "start_favorit":
            query.edit_message_text(
                text="Wähle zunächst eine Oberkategorie:",
                reply_markup=self.set_markup_abo_fave()
            )
        elif query.data == "no_favorit":
            query.edit_message_text(
                text="Kein Problem. Du kannst auch noch später über den Befehl /set_favorit einen Favoriten "
                     "festlegen. "
            )

    # sends start message when a user first starts a conversation with the bot or sends '/start' to the bot
    def message_start(self, update: Update, context: CallbackContext):
        with open("Start.html", "r", encoding="utf-8") as f:
            text = f.read()

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode=ParseMode.HTML
        )

        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("JA", callback_data="start_favorit")],
                [InlineKeyboardButton("NEIN", callback_data="no_favorit")]
            ]
        )
        # add user to date base to notify about major updates
        User.insert_user(chat_id=str(update.effective_chat.id), name=str(update.effective_chat.username))

        # sleep before asking to add favorit
        sleep(7)
        update.message.reply_text('Möchtest du jetzt einen Favoriten auswählen?', reply_markup=reply_markup)

    # sends help message when a user sends '/help' to the bot
    def message_help(self, update: Update, context: CallbackContext):
        with open("Start.html", "r", encoding="utf-8") as f:
            text = f.read()

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode=ParseMode.HTML
        )

    # initiates inline button process to set a favorite abo box
    def message_set_abo_fave(self, update: Update, _: CallbackContext):
        reply_markup = self.set_markup_abo_fave()
        update.message.reply_text('Wähle zunächst eine Oberkategorie:', reply_markup=reply_markup)
        # temporary use to implement a user database for announcing updates
        User.insert_user(chat_id=str(update.effective_chat.id), name=str(update.effective_chat.username))

    # let the user remove data collected about him/her (chat_id, user_name, stored favorite and reminder)
    def message_remove_user(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        User.remove_user(chat_id=str(chat_id))
        UserFavorite.remove_user(chat_id=str(chat_id))
        Reminder.remove_reminder(chat_id=str(chat_id))
        text = "Deine Daten wurden erfolgreich gelöscht. Jetzt musst du nur noch den Bot selbst löschen."
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text
        )

    # sends reply with the current abo favorit if one is set, else it replies with a help message
    def message_get_abo_fave(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        fave = UserFavorite.get_from_chat_id(chat_id=str(chat_id))
        if fave:
            text = f"Dein aktueller Abo-Favorit ist \"{fave.box_name}\"."
        else:
            text = f"Du hast noch keinen Favoriten festgelegt. Lege einen Favoriten über /set_favorit fest.\n"
        context.bot.send_message(
            chat_id=chat_id,
            text=text
        )

    # either sending the current weeks details (name, ingredients, ingredient-urls) of an abo box
    # passed as arguments (name, size), or, if no arguments were passed, sending the details of
    # the stored favorit
    def message_get_abo_details_cur_week(self, update: Update, context: CallbackContext):
        week = "diese_woche"
        chat_id = update.effective_chat.id
        box = self.get_abo_details(chat_id=str(chat_id), context_args=context.args, week=week)
        if isinstance(box, tuple):
            text = AboBox.get_abo_details(week=week, box_name=box[0], box_size=box[1])
        else:
            text = box
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

    # same as message_get_abo_details_cur_week but for the next calendar week
    def message_get_abo_details_next_week(self, update: Update, context: CallbackContext):
        week = "naechste_woche"
        chat_id = update.effective_chat.id
        box = self.get_abo_details(chat_id=str(chat_id), context_args=context.args, week=week)
        if isinstance(box, tuple):
            text = AboBox.get_abo_details(week=week, box_name=box[0], box_size=box[1])
        else:
            text = box
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

    # send message with all currently available abo boxes
    def message_get_all_box_names(self, update: Update, context: CallbackContext):
        boxes_dic = self.get_all_boxes_sorted()
        boxes_url = AboBox.boxes_lst[0].url
        text = "<b>Alle Abos dieser und nächster Woche:</b>\n\n"
        for key, value in boxes_dic.items():
            text += f"<b>{key}</b>\n"
            text += "\n".join(value) + "\n\n"
        text += f'\n\n<a href="{boxes_url}">Zu den Abos</a>'
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode=ParseMode.HTML
        )
        return boxes_dic

    # this method is called by the app scheduler and sends a reminder message for the users' favorite
    def send_reminder_message(self, context: CallbackContext):
        text = "<b>Automatische Erinnerung für:</b>\n\n"
        job = context.job
        reminder = Reminder.get_from_chat_id(chat_id=str(context.job.name))
        box_name = reminder.box_name.lower()
        text += AboBox.get_abo_details(week="diese_woche", box_name=box_name, box_size='')
        context.bot.send_message(job.context, text=text, parse_mode=ParseMode.HTML)

    # checks the arguments passed by the user and, if correct, adds a weekly reminder
    # for his/her favorite to the app scheduler
    def message_set_reminder(self, update: Update, context: CallbackContext):
        days_to_int = {
            "montags": 0,
            "dienstags": 1,
            "mittwochs": 2,
            "donnerstags": 3,
            "freitags": 4,
            "samstags": 5,
            "sonntags": 6
        }
        chat_id = update.effective_chat.id

        # transform days, hours and minutes from string to int if they were passed correctly else, return help messsage
        try:
            # transform days using the translation dict above
            day_int = None
            for key, value in days_to_int.items():
                if context.args[0].lower() in key:
                    day_int = value
            # transform hours and minutes
            t = str(context.args[1]).split(':')
            hour, minute = int(t[0]), int(t[1])
        except (IndexError, ValueError):
            update.message.reply_text('Falsche Eingabe. Versuche z. B.: /erinnere_mich montags 18:10')
            return

        # check if the given ints are valid time ints
        if day_int not in [0, 1, 2, 3, 4, 5, 6]:
            update.message.reply_text('Bitte gib einen Wochentag für die Wiederholug an, w. z. B. "mittwochs"')
            return
        elif hour not in range(6, 24, 1):
            update.message.reply_text('Da der Server zwischen 0 Uhr und 6 Uhr aus ist, können nur Stunden zwischen '
                                      '6 Uhr und 23 Uhr angegeben werden.')
            return
        elif minute not in range(0, 60, 1):
            update.message.reply_text('Bitte gib eine korrekte Minute an, zu der die Erinnerung erscheinen soll..')
            return

        # check if the user has set a favorite
        try:
            box_name = UserFavorite.get_from_chat_id(chat_id=str(chat_id)).box_name
        except AttributeError:
            text = f"Du hast noch keinen Favoriten festgelegt. Lege einen Favoriten über /set_favorit fest.\n"
            update.message.reply_text(text)
            return

        # check if another reminder/job was set and if, replace it
        job_removed = self.remove_job_if_exists(str(chat_id), context)

        # set reminder
        Reminder.insert_reminder(chat_id=str(chat_id), day_of_week=day_int, hour=hour, minute=minute, box_name=box_name)
        # specify your timezone
        context.job_queue.run_daily(self.send_reminder_message,
                                    time=time(hour=hour, minute=minute, second=5, tzinfo=timezone('Europe/Berlin')),
                                    days=([day_int]),
                                    context=str(chat_id),
                                    name=str(chat_id)
                                    )

        # get written weekday from integer weekday
        week_day = list(days_to_int.keys())[list(days_to_int.values()).index(day_int)]
        text = f'Erinnerung für {box_name} der jeweiligen Woche erfolgreich auf {week_day} {hour:02d}:{minute:02d} ' \
               f'Uhr festgelegt!'

        # add a note to text, if another reminder was replaced
        if job_removed:
            text += "\n\nDie alte Erinnerung wurde ersetzt."

        update.message.reply_text(text)

    # let the user remove his/her current reminder
    def message_remove_reminder(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        job_removed = self.remove_job_if_exists(str(chat_id), context)
        text = 'Erinnerung erfolgreich gelöscht!' if job_removed else 'Es gibt keine aktive Erinnerung.'
        update.message.reply_text(text)

    # sends the currently set reminder back to the user
    def message_get_reminder(self, update: Update, context: CallbackContext):
        days_to_int = {
            "montags": 0,
            "dienstags": 1,
            "mittwochs": 2,
            "donnerstags": 3,
            "freitags": 4,
            "samstags": 5,
            "sonntags": 6
        }
        chat_id = update.effective_chat.id
        reminder = Reminder.get_from_chat_id(chat_id=str(chat_id))
        try:
            week_day = list(days_to_int.keys())[list(days_to_int.values()).index(reminder.day_of_week)]
            text = f"Du wirst aktuell {week_day} um {reminder.hour:02d}:{reminder.minute:02d} Uhr an das " \
                   f"Abo \"{reminder.box_name}\" erinnert."
        except AttributeError:
            text = "Du hast noch keine Erinnerung festgelegt. Lege jetzt eine Erinnerung fest: /erinnere_mich"
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

    # removes job with given name (chat_id) from app scheduler and sql_table and returns true if a job was removed
    def remove_job_if_exists(self, chat_id: str, context: CallbackContext) -> bool:
        current_jobs = context.job_queue.get_jobs_by_name(chat_id)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
        Reminder.remove_reminder(chat_id=chat_id)
        return True
