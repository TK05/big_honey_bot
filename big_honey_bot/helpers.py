import hashlib
import json
from datetime import datetime
import platform
from zoneinfo import ZoneInfo

from big_honey_bot.config.main import setup, OUTPUT_PATH


platform_hr_min_fmt = "%#I:%M" if platform.system() == 'Windows' else '%-I:%M'
platform_day_fmt = "%#d" if platform.system() == 'Windows' else '%-d'
platform_mo_day_fmt = "%#m/%#d" if platform.system() == 'Windows' else "%-m/%-d"

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


def validate_timezone(tz):
    
    if isinstance(tz, ZoneInfo):
        return tz
    elif isinstance(tz, str):
        return ZoneInfo(tz)
    else:
        raise AttributeError


def change_timezone(dt, tz=setup['timezone']):
    
    tz = validate_timezone(tz)
    
    return dt.astimezone(tz)


def add_timezone_to_datetime(dt, tz=setup['timezone']):
        
        tz = validate_timezone(tz)

        return dt.astimezone(tz)


def get_datetime(dt=None, add_tz=False, tz=setup['timezone']):

    if not dt:
        dt = datetime.now()
    elif isinstance(dt, list):
        dt = datetime(*dt)
    elif isinstance(dt, dict):
        dt = datetime(**dt)
    
    if add_tz:
        dt = add_timezone_to_datetime(dt)
    
    return dt


def get_datetime_from_timestamp(ts=None, add_tz=False, tz=setup['timezone']):

    if not ts:
        ts = datetime.timestamp(datetime.now())
    
    # check if timestamp is int, create datetime obj if so
    try:
        dt = datetime.fromtimestamp(int(ts))
    except (TypeError, ValueError) as e:
        raise e

    if add_tz:
        dt = add_timezone_to_datetime(dt)

    return dt


def get_timestamp_from_datetime(dt=None):

    if not dt:
        dt = datetime.now()
    
    return int(dt.timestamp())


def get_datetime_from_str(dt_str, fmt, add_tz=False, tz=setup['timezone']):

    dt = datetime.strptime(dt_str, fmt)
    
    if add_tz:
        dt = add_timezone_to_datetime(dt=dt, tz=tz)
    
    return dt


def get_str_from_datetime(dt=None, fmt='%D %I:%M %p', add_tz=False, tz=setup['timezone']):

    if not dt:
        dt = datetime.now()
    
    if add_tz:
        dt = add_timezone_to_datetime(dt=dt, tz=tz)
    
    return datetime.strftime(dt, format(fmt))


def timestamps_are_same_day(ts_1, ts_2, tz):
    
    date_1 = get_datetime_from_timestamp(ts_1, tz)
    date_2 = get_datetime_from_timestamp(ts_2, tz)

    return date_1.date() == date_2.date()
