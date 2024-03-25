import os
from datetime import timedelta

from gcsa.event import Event

from big_honey_bot.helpers import get_datetime
from big_honey_bot.events.main import create_event


def make_new_event(event, seconds=60):
    now = get_datetime()
    new_event = Event(summary=event.summary, start=(now + timedelta(seconds=seconds)),
                      end=(now + timedelta(seconds=seconds+61)), description=event.description)
    create_event(new_event)
    print(f"{os.path.basename(__file__)}: Event created: {event.summary}")
