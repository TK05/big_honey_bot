import json

from dotenv import load_dotenv
from gcsa.serializers.event_serializer import EventSerializer

from big_honey_bot.helpers import description_tags, get_dict_from_json_file
from big_honey_bot.events.helpers import create_service


FILE_NAME = 'all_events.json'


def update_calendar(schedule):
    service = create_service()

    for utc, event_data in schedule.items():
        cal_event = {
            "start": event_data["start"],
            "end": event_data["end"],
            "summary": event_data["summary"],
            "description": f"{description_tags['meta_start']}{json.dumps(event_data['meta'])}{description_tags['meta_end']}"
                           f"{description_tags['body_start']}{event_data['description']}{description_tags['body_end']}",
            "location": event_data["location"]
        }

        service.add_event(EventSerializer.to_object(cal_event))
        print(f"{utc} - {event_data['summary']}")


if __name__ == '__main__':
    load_dotenv()
    schedule_in = get_dict_from_json_file(FILE_NAME)
    update_calendar(schedule_in)
