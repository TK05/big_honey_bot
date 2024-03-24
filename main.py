import logging
from pathlib import Path
from dotenv import load_dotenv

from config import DEBUG
from bots import manage_events_bot


def setup_logger(log_path):
    
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


if __name__ == "__main__":
    
    # setup logging
    log_filename = "big_honey_bot.log"
    log_file = Path.cwd().joinpath(log_filename)
    setup_logger(log_file)

    # load from .env
    load_dotenv()

    # run main bot
    manage_events_bot.run()
