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
            # meta start delimeter = {meta_begin} +1 newline, meta end delimeter = {meta_end} +1 newline
            # body start delimeter = {body_begin} +1 newline, meta end delimeter = {body_end} +1 newline
            "description": f"{{meta_begin}}\n{json.dumps(event_data['meta'])}\n{{meta_end}}\n\n{{body_begin}}\n{event_data['description']}\n{{body_end}}",
            "location": event_data["location"]
        }

        service.add_event(EventSerializer.to_object(cal_event))


if __name__ == '__main__':

    with open('../json_output/all_events.json', 'r') as file:
        raw_schedule = json.load(file)
        update_calendar(raw_schedule)
