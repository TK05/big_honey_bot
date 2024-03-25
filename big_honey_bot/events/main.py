import json
import re
from datetime import timedelta
from abc import ABC
from html.parser import HTMLParser

from gcsa.serializers.event_serializer import EventSerializer

from big_honey_bot.helpers import description_tags, create_hash, get_datetime
from big_honey_bot.events.helpers import create_service


class HTMLFilter(HTMLParser, ABC):
    text = ""

    def handle_data(self, data):
        self.text += data


def add_meta_and_body(event):
    def set_meta_and_body(ev):
        meta = json.loads(ev.description[ev.description.find(start := description_tags['meta_start']) + len(start):ev.description.find(description_tags['meta_end'])])
        setattr(event, 'meta', meta)
        body = (ev.description[ev.description.find(start := description_tags['body_start']) + len(start):ev.description.find(description_tags['body_end'])])
        setattr(event, 'body', body)

        return event

    if event.description:
        try:
            event = set_meta_and_body(event)
        # Handle when event touched via UI and description gets populated with HTML tags
        except json.JSONDecodeError:
            desc_re = re.sub('<br\s*?\/?>', '\n', event.description)
            desc_tag = HTMLFilter()
            desc_tag.feed(desc_re)
            event.description = desc_tag.text

            event = set_meta_and_body(event)


def get_all_events():
    service = create_service()

    return service.get_events(order_by='startTime', single_events=True)


def get_all_events_with_meta():
    service = create_service()
    events = service.get_events(order_by='startTime', single_events=True)
    all_events = []

    for event in events:
        add_meta_and_body(event)
        all_events.append(event)

    return all_events


def get_previous_event(penultimate=False, days=30):
    service = create_service()
    now = get_datetime()
    events = service.get_events((now - timedelta(days=days)),
                                now, order_by='startTime', single_events=True)

    # Return penultimate event if requested, else return last event
    event = None
    for event in list(events)[:-1 if penultimate else None]:
        pass

    if event:
        add_meta_and_body(event)

    return event


def get_event(event_id):
    service = create_service()
    event = service.get_event(event_id)
    add_meta_and_body(event)

    return event


def get_next_event():
    try:
        next_event = next(get_all_events())
        add_meta_and_body(next_event)
    except StopIteration:
        next_event = None

    return next_event


def find_event(query, past=None):
    service = create_service()
    event = next(service.get_events(time_min=past, query=query))
    add_meta_and_body(event)

    return event


def find_events_by_meta(**kwargs):
    all_events = get_all_events_with_meta()

    matches = []

    for event in all_events:
        if all(item in event.meta.items() for item in kwargs.items()):
            matches.append(event)
    
    return matches


def create_event(event_data):
    service = create_service()
    service.add_event(event_data)


def update_event(event):
    service = create_service()

    # Update hashes before updating event
    event.meta['title_hash'] = create_hash(event.summary)
    event.meta['body_hash'] = create_hash(event.body)

    # Update description w/ new hashes and any body changes
    event.description = f"{description_tags['meta_start']}{json.dumps(event.meta)}{description_tags['meta_end']}" \
                        f"{description_tags['body_start']}{event.body}{description_tags['body_end']}"
    service.update_event(event)


def update_event_serial(event_json):
    service = create_service()
    service.update_event(EventSerializer.to_object(event_json))


def delete_event(event):
    service = create_service()
    service.delete_event(event)


def delete_all_events():
    service = create_service()
    events = get_all_events()

    for event in events:
        service.delete_event(event)
