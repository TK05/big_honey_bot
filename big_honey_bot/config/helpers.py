import logging
import time
from pathlib import Path
from distutils.util import strtobool

from dotenv import dotenv_values, load_dotenv


OUTPUT_PATH = Path.cwd().joinpath("out")

if not OUTPUT_PATH.exists():
    OUTPUT_PATH.mkdir()


def get_env(env_key):
    """General function to allow calling refreshed env vars."""
    env = dotenv_values(Path('.env'))

    try:
        # some env vars are boolean, try converting first
        return bool(strtobool(env.get(env_key)))
    except ValueError:
        return env.get(env_key)


def reload_env(sleep_time_sec):
    while True:
        load_dotenv()
        time.sleep(sleep_time_sec)


def get_all_env():
    return dotenv_values(Path('.env'))


def configure_logging(log_path):
    
    # create logger
    logger = logging.getLogger()

    # create file handler
    fh = logging.FileHandler(filename=log_path, encoding='utf-8')
    
    # set debug levels
    if get_env('DEBUG'):
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
