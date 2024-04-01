import logging
import asyncio

from big_honey_bot.main import run_bhb
from big_honey_bot.config.main import OUTPUT_PATH, LOG_FILENAME, ENV_RELOAD_INTERVAL_SEC
from big_honey_bot.config.helpers import configure_logging, reload_env, get_env, get_pname_fname_str


if __name__ == "__main__":
    
    # setup logging
    log_file = OUTPUT_PATH.joinpath(LOG_FILENAME)
    configure_logging(log_file)
    logger = logging.getLogger(get_pname_fname_str(__file__))

    logger.info("Starting big_honey_bot....")

    # create thread to reload .env every ENV_RELOAD_INTERVAL_SEC
    asyncio.create_task(reload_env(ENV_RELOAD_INTERVAL_SEC))

    if get_env('DEBUG'):
        from big_honey_bot.config.helpers import get_all_env

        logger.debug(f"All env variables: {get_all_env()}")

    # start run_bhb main event loop
    asyncio.run(run_bhb())
