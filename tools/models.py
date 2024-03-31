from datetime import datetime, timedelta

from big_honey_bot.helpers import create_hash, get_str_from_datetime, platform_hr_min_fmt
from big_honey_bot.threads.helpers import create_templatized_headline


SECONDS_TIL_END = 61


class GameEvent:

    def __init__(self, event_data, event_type, start, game_ts, description, in_playoffs):
        self._event_data = event_data
        self._event_type = event_type
        self._description = description
        self._in_playoffs = in_playoffs
        self._game_ts = int(game_ts)
        self._start = self._validate_datetime(start)
        self._end = (self._start + timedelta(seconds=SECONDS_TIL_END))
        self._location = f"{self._event_data['arena']} - {self._event_data['city']}"
        self._summary = create_templatized_headline(
            self._event_type, self._event_data['home_away'], self._event_data['opponent'], self._in_playoffs
            )
        self._meta = None
        self._time_fmt = '%G-%m-%dT%H:%M:%S'

    
    @property
    def meta(self):
        self.add_meta()
        return self._meta
    
    
    def _validate_datetime(self, time_value):
        if not isinstance(time_value, datetime):
            raise TypeError("Time values must be a datetime.")
        elif time_value.tzinfo == None:
            raise ValueError("Time values must have a timezone.")
        
        return time_value
    
    
    def add_meta(self, **kwargs):
        meta = {
            "game_utc": self._game_ts,
            "event_type": self._event_type,
            "post_time": get_str_from_datetime(dt=self._start, fmt=f'{platform_hr_min_fmt} %p'),
            **self._event_data
        }
        meta.update(kwargs)
        self._meta = meta

    
    def _add_hashes_to_meta(self):
        if self._meta == None:
            raise AttributeError("Cannot hash meta when meta=None.")
        
        hashes = {
            "title_hash": create_hash(self._summary),
            "body_hash": create_hash(self._description)
        }

        self._meta.update(hashes)
    

    def _clean_meta_for_google_cal(self):
        # keys that will end up in meta on google cal event
        # TODO: probably store this somewhere else
        meta_keys_keep = ["game_start", "espn_id", "nba_id", "home_away", "opponent", "game_utc",
                "event_type", "title_hash", "body_hash", "win", "lose"]
        
        new_meta = {}
        
        for key in self._meta.keys():
            if key in meta_keys_keep:
                new_meta[key] = self._meta[key]
        
        self._meta = new_meta

    
    def as_dict_for_google_cal(self):
        ret_dict = {
            'start': {
                'dateTime': self._start.strftime(self._time_fmt),
                'timeZone': self._start.tzname()
            },
            'end': {
                'dateTime': self._end.strftime(self._time_fmt),
                'timeZone': self._end.tzname()
            },
            'location': self._location,
            'summary': self._summary,
            'description': self._description
        }

        self.add_meta()
        self._clean_meta_for_google_cal()
        self._add_hashes_to_meta()
        ret_dict.update({"meta": self._meta})

        return ret_dict
