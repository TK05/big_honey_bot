import json
from gcsa.serializers.event_serializer import EventSerializer

from events.google_service import create_service


def update_calendar(schedule):
    service = create_service()

    for utc, event_data in schedule.items():
        cal_event = {
            "id": utc,
            "start": event_data["start"],
            "summary": event_data["summary"],
            "description": f"{event_data['meta']}\n\n{event_data['description']}",
            "location": event_data["location"]
        }

        service.add_event(EventSerializer.to_object(cal_event))


if __name__ == '__main__':

    with open('../json_output/all_events.json', 'r') as file:
        raw_schedule = json.load(file)
        update_calendar(raw_schedule)
