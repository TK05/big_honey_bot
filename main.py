import logging
from dotenv import load_dotenv

from config import DEBUG, OUTPUT_PATH
from bots import manage_events_bot


def configure_logging(log_path):
    
    # create logger
    logger = logging.getLogger()

    # create file handler
    fh = logging.FileHandler(filename=log_path, encoding='utf-8')
    
    # set debug levels
    if DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s: %(message)s')

    # add formatter to file handler
    fh.setFormatter(formatter)

    # add handler to logger
    logger.addHandler(fh)

    # quiet spammy loggers
    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


if __name__ == "__main__":
    
    # setup logging
    log_filename = "big_honey_bot.log"
    log_file = OUTPUT_PATH.joinpath(log_filename)
    configure_logging(log_file)

    # load from .env
    load_dotenv()

    # run main bot
    manage_events_bot.run()