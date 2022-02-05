import logging
import sys
from TBotEngine import TBot
from AboBox import AboBox
from scheduler import Scheduler
from datetime import time
from pytz import timezone


def main():
    # configurate the parent logger
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # scrape all abos from the given website by html-tags, store them as instances of class AboBox and collect all in
    # AboBox.boxes_lst
    AboBox.get_all_boxes()

    # As the bot needs to run in another thread for local use of the app update.start_pulling() and not update.idle()
    # is used. Problem is, that there is no clean way to stop update.start_pulling() without calling update.idle() from
    # within the main thread before. So the try/exception-handling here is just a dirty workaround, till I or someone
    # implemented a better solution.
    try:
        # start the telegram bot and load stored reminders into the app scheduler
        bot = TBot()
        bot.start_bot()
        bot.load_reminders()

        # start scheduler to scrape the abo boxes every day at the given time
        tz = timezone("Europe/Berlin")
        schedule = Scheduler(tzinfo=tz, n_threads=0)
        schedule.daily(time(hour=12, minute=36, tzinfo=tz), AboBox.get_all_boxes)
        while True:
            schedule.exec_jobs()

    except KeyboardInterrupt:
        sys.exit()


if __name__ == '__main__':
    main()
