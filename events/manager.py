import json
import re
import os
from abc import ABC
from html.parser import HTMLParser
from gcsa.serializers.event_serializer import EventSerializer

from events.google_service import create_service
from tools.toolkit import description_tags, create_hash


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
            desc_re = re.sub('<br\s*?>', '\n', event.description)
            desc_tag = HTMLFilter()
            desc_tag.feed(desc_re)
            event.description = desc_tag.text

            event = set_meta_and_body(event)


def get_all_events():
    service = create_service()

    return service.get_events(order_by='startTime', single_events=True)


def get_event(event_id):
    service = create_service()
    event = service.get_event(event_id)
    add_meta_and_body(event)
    print(f"{os.path.basename(__file__)}: Event found: {event.id} - {event.summary}")

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

    return next(service.get_events(time_min=past, query=query))


def create_event(event_data):
    service = create_service()
    service.add_event(event_data)
    print(f"{os.path.basename(__file__)}: Event created: {event_data.summary}")


def update_event(event):
    service = create_service()

    # Update hashes before updating event
    event.meta['title_hash'] = create_hash(event.summary)
    event.meta['body_hash'] = create_hash(event.body)

    # Update description w/ new hashes and any body changes
    event.description = f"{description_tags['meta_start']}{json.dumps(event.meta)}{description_tags['meta_end']}" \
                        f"{description_tags['body_start']}{event.body}{description_tags['body_end']}"
    service.update_event(event)
    print(f"{os.path.basename(__file__)}: Event updated: {event.id} - {event.summary}")


def update_event_serial(event_json):
    service = create_service()
    service.update_event(EventSerializer.to_object(event_json))
    print(f"{os.path.basename(__file__)}: Event serial updated")


def delete_event(event):
    service = create_service()
    service.delete_event(event)
    print(f"{os.path.basename(__file__)}: Event deleted: {event.id} - {event.summary}")


def delete_all_events():
    service = create_service()
    events = get_all_events()

    for event in events:
        service.delete_event(event)
