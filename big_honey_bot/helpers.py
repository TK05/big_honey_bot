import hashlib
import json
import time

from dotenv import load_dotenv

from big_honey_bot.config.main import OUTPUT_PATH


description_tags = {
    "meta_start": "{meta_begin}\n",
    "meta_end": "\n{meta_end}",
    "body_start": "\n{body_begin}\n",
    "body_end": "\n{body_end}",
    "our_record": "{our_rec}",
    "opp_record": "{opp_rec}",
    "date_and_time": "{date_time}",
    "starters": "{starters}",
    "injuries": "{injuries}",
    "odds": "{odds}",
    "referees": "{referees}",
    "daily_games": "{daily_games}",
    "playoff_series": "{playoff_series}",
    "playoff_teams": "{playoff_teams}"
}


def write_dict_to_json_file(file_name, data):
    
    OUTPUT_PATH.mkdir(exist_ok=True)

    with open(OUTPUT_PATH.joinpath(file_name), 'w') as f:
        json.dump(data, f, indent=4)


def get_dict_from_json_file(file_name):
    if not OUTPUT_PATH.joinpath(file_name).exists():
        ret_dict = {}
    else:
        with open(OUTPUT_PATH.joinpath(file_name), 'r') as f:
            ret_dict = json.load(f)

    return ret_dict


def create_hash(string):
    return hashlib.md5(string.encode()).hexdigest()


def hash_match(string, hash_in):
    return hash_in == hashlib.md5(string.encode()).hexdigest()


def reload_env(sleep_time_sec):
    while True:
        load_dotenv()
        time.sleep(sleep_time_sec)