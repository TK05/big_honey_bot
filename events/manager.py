import json
from gcsa.serializers.event_serializer import EventSerializer

from events.google_service import create_service
from tools.toolkit import description_tags, create_hash


def add_meta_and_body(event):
    if event.description:
        meta = json.loads(event.description[event.description.find(start:=description_tags['meta_start'])+len(start):event.description.find(description_tags['meta_end'])])
        setattr(event, 'meta', meta)
        body = (event.description[event.description.find(start:=description_tags['body_start'])+len(start):event.description.find(description_tags['body_end'])])
        setattr(event, 'body', body)


def get_all_events():
    service = create_service()

    return service.get_events(order_by='startTime', single_events=True)


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
