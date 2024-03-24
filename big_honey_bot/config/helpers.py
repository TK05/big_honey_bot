from pathlib import Path
from distutils.util import strtobool

from dotenv import dotenv_values


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
