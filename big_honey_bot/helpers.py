import hashlib
import json
from datetime import datetime

import pytz

from big_honey_bot.config.main import setup, OUTPUT_PATH


description_tags = {
    "meta_start": "{meta_begin}\n",
    "meta_end": "\n{meta_end}",
    "body_start": "\n{body_begin}\n",
    "body_end": "\n{body_end}",
    "starters": "{starters}",
    "injuries": "{injuries}",
    "odds": "{odds}",
    "referees": "{referees}",
    "daily_games": "{daily_games}"
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


def convert_to_timezone(tz):
    # check if tz is already a pytz.timezone object or string, return as pytz.timezone
    try:
        tz.zone
    except AttributeError:
        tz = pytz.timezone(tz)
    
    return tz

def add_timezone_to_datetime(datetime, tz=setup['timezone']):
        return convert_to_timezone(tz).localize(datetime)


def get_datetime(datetime=datetime.now(), add_tz=False, tz=setup['timezone']):
    
    if add_tz:
        datetime = add_timezone_to_datetime(datetime)
    
    return datetime


def get_datetime_from_timestamp(timestamp=datetime.timestamp(datetime.now()), add_tz=False, tz=setup['timezone']):
    
    # check if timestamp is int, create datetime obj if so
    try:
        dt = datetime.fromtimestamp(int(timestamp))
    except (TypeError, ValueError) as e:
        raise e

    if add_tz:
        dt = add_timezone_to_datetime(dt)

    return dt


def get_timestamp_from_datetime(datetime=datetime.now()):
    
    return int(datetime.timestamp())


def get_datetime_from_str(dt_str, fmt, add_tz=False, tz=setup['timezone']):
    
    if add_tz:
        tz = convert_to_timezone(tz)
        return tz.localize(datetime.strptime(dt_str, fmt))
    
    return datetime.strptime(dt_str, fmt)


def get_str_from_datetime(dt=datetime.now(), fmt='%D %I:%M %p', add_tz=False, tz=setup['timezone']):
    
    if add_tz:
        return datetime.strftime(dt.astimezone(tz=convert_to_timezone(tz)), format(fmt))
    
    return datetime.strftime(dt, format(fmt))


def timestamps_are_same_day(ts_1, ts_2, tz):
    
    date_1 = get_datetime_from_timestamp(ts_1, tz)
    date_2 = get_datetime_from_timestamp(ts_2, tz)

    return date_1.date() == date_2.date()
