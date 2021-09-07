from gcsa.event import Event
from gcsa.serializers.event_serializer import EventSerializer

from events.google_service import create_service


def get_all_events():
    service = create_service()

    return service.get_events()


def get_event(event_id):
    service = create_service()

    return service.get_event(event_id)


def get_next_event():
    service = create_service()
    all_events = service.get_events()

    return next(all_events)


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
