import logging
import time
from pathlib import Path

from dotenv import dotenv_values, load_dotenv


OUTPUT_PATH = Path.cwd().joinpath("out")

if not OUTPUT_PATH.exists():
    OUTPUT_PATH.mkdir()


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).

    True values are: ('y', 'yes', 't', 'true', 'on', '1').
    False values are: ('n', 'no', 'f', 'false', 'off', '0').
    Raises ValueError if 'val' is anything else.
    """
    
    try:
        val = val.lower()
    except AttributeError:
        raise

    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"Invalid truth value {val}")


def get_env(env_key):
    """General function to allow calling refreshed env vars."""
    
    env = dotenv_values(Path('.env'))
    env_val = env.get(env_key)

    try:
        # some env vars are boolean, try converting first
        return bool(strtobool(env_val))
    except (ValueError, AttributeError):
        return env_val


def reload_env(sleep_time_sec):
    while True:
        load_dotenv()
        update_logger_level()
        time.sleep(sleep_time_sec)


def get_all_env():
    return dotenv_values(Path('.env'))


def get_pname_fname_str(fname):
    
    abs_path = Path(fname)
    
    return ''.join(abs_path.parts[-2:])


def update_logger_level():
    logger = logging.getLogger()
    
    # set debug levels
    if get_env('DEBUG'):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


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
