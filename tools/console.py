from datetime import datetime, timedelta
from gcsa.event import Event
from events.manager import create_event


def make_new_event(event, seconds=60):
    now = datetime.now()
    new_event = Event(summary=event.summary, start=(now + timedelta(seconds=seconds)),
                      end=(now + timedelta(seconds=seconds+61)), description=event.description)
    create_event(new_event)
