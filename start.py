import logging
import threading

from big_honey_bot.main import run as run_bhb
from big_honey_bot.config.main import OUTPUT_PATH, LOG_FILENAME, ENV_RELOAD_INTERVAL_SEC
from big_honey_bot.config.helpers import configure_logging, reload_env, get_env, get_pname_fname_str


if __name__ == "__main__":
    
    # setup logging
    log_file = OUTPUT_PATH.joinpath(LOG_FILENAME)
    configure_logging(log_file)
    logger = logging.getLogger(get_pname_fname_str(__file__))

    # create thread to reload .env every minute
    reload_env_thread = threading.Thread(target=reload_env, args=(ENV_RELOAD_INTERVAL_SEC,), daemon=True)
    reload_env_thread.start()

    logger.info("Starting big_honey_bot....")

    if get_env('DEBUG'):
        from big_honey_bot.config.helpers import get_all_env

        logger.debug(f"All env variables: {get_all_env()}")

    # run bhb main event loop
    run_bhb()
