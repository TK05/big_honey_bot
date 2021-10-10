import json
from gcsa.serializers.event_serializer import EventSerializer

from events.google_service import create_service

META_BEGIN = '{meta_begin}\n'
META_END = '\n{meta_end}'
BODY_BEGIN = '{body_begin}\n'
BODY_END = '\n{body_end}'


def add_meta_and_body(event):
    if event.description:
        meta = json.loads(event.description[event.description.find(start:=META_BEGIN)+len(start):event.description.find(META_END)])
        setattr(event, 'meta', meta)
        body = (event.description[event.description.find(start:=BODY_BEGIN)+len(start):event.description.find(BODY_END)])
        setattr(event, 'body', body)


def get_all_events():
    service = create_service()

    return service.get_events()


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


def find_event(query):
    service = create_service()

    return next(service.get_events(query=query))


def create_event(event_data):
    service = create_service()
    service.add_event(event_data)


def update_event(event):
    service = create_service()
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
