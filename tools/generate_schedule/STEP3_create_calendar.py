import json
from gcsa.serializers.event_serializer import EventSerializer

from events.google_service import create_service
from tools.toolkit import description_tags


def update_calendar(schedule):
    service = create_service()

    for utc, event_data in schedule.items():
        cal_event = {
            "id": utc,
            "start": event_data["start"],
            "summary": event_data["summary"],
            "description": f"{description_tags['meta_start']}{json.dumps(event_data['meta'])}{description_tags['meta_end']}"
                           f"{description_tags['body_start']}{event_data['description']}{description_tags['body_end']}",
            "location": event_data["location"]
        }

        service.add_event(EventSerializer.to_object(cal_event))


if __name__ == '__main__':

    with open('../json_output/all_events.json', 'r') as file:
        raw_schedule = json.load(file)
        update_calendar(raw_schedule)
