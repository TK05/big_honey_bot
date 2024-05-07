import logging
import threading

from big_honey_bot.main import run_bhb
from big_honey_bot.config.main import OUTPUT_PATH, LOG_FILENAME
from big_honey_bot.config.helpers import configure_logging, reload_env, get_env, get_pname_fname_str


def main():
    # create thread to reload .env every ENV_RELOAD_INTERVAL_SEC
    reload_env_thread = threading.Thread(target=reload_env)
    reload_env_thread.start()

    # start run_bhb main event loop
    logger.info("Starting big_honey_bot....")
    run_bhb()


if __name__ == "__main__":
    
    # setup logging
    log_file = OUTPUT_PATH.joinpath(LOG_FILENAME)
    configure_logging(log_file)
    logger = logging.getLogger(get_pname_fname_str(__file__))

    if get_env('DEBUG'):
        from big_honey_bot.config.helpers import get_all_env

        logger.debug(f"All env variables: {get_all_env()}")

    # start run_bhb main event loop
    main()
