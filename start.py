import logging
import threading

from big_honey_bot.main import run as run_bhb
from big_honey_bot.helpers import reload_env
from big_honey_bot.config.main import DEBUG, OUTPUT_PATH


ENV_RELOAD_INTERVAL_SEC = 60
LOG_FILENAME = "big_honey_bot.log"


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
    log_file = OUTPUT_PATH.joinpath(LOG_FILENAME)
    configure_logging(log_file)

    # create thread to reload .env every minute
    reload_env_thread = threading.Thread(target=reload_env, args=(ENV_RELOAD_INTERVAL_SEC,), daemon=True)
    reload_env_thread.start()

    # run bhb main event loop
    run_bhb()
