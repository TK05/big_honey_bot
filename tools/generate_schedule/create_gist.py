import json
import os
from datetime import datetime
import requests

from handle_gists.gists import update_gist
from config import gists


USERNAME = os.environ['GISTS_USERNAME']
API_TOKEN = os.environ['GISTS_API']

gists_url = "https://api.github.com/gists"
gists_header = {'X-Github-username': USERNAME, 'Content-Type': 'application/json',
                'Authorization': f"token {API_TOKEN}"}


def create_gist(schedule_json, filename='schedule.json', public=False):
    """Creates or updates a Gist using the supplied schedule_json.
    If no schedule Gist in config, creates a new Gist and prints filename, id and url to console.
    If schedule in Gist, updates current Gist.
    """

    # If schedule data found in config
    if gists['schedule']['filename'] and gists['schedule']['id']:
        print('Schedule gist found in config, updating current Gist')
        res_html = update_gist(datetime.now().strftime('%c'), 'schedule', schedule_json)
        print(f"Updated Schedule Gist @ {res_html}")
        return

    # If no schedule data found in config
    data = json.dumps({
        "description": f"Updated: {datetime.now().strftime('%c')}",
        "public": public,
        "files": {
            f"{filename}": {
                "content": f"{schedule_json}"
            }
        }
    })

    response = requests.post(gists_url, data=data, headers=gists_header)

    if response.status_code == 201:
        response_data = response.json()
        print(f"New Gist for schedule @ {response_data['html_url']}")
        print("Update config/config.py gists['schedule'] with:")
        print(f"filename: {filename}")
        print(f"id: {response_data['id']}")

    else:
        json_data = json.dumps(response.json(), indent=4)
        try:
            os.mkdir('../tmp')
        except FileExistsError:
            pass
        with open('../tmp/create_gist_failed.txt', 'w') as f:
            f.write(f'Status Code: {response.status_code}\n\n'
                    f'{json_data}')

        print('Gist creation FAILED')
        print('Check tools/tmp/create_gist_failed.txt for more details.')


if __name__ == '__main__':

    with open('../json_output/schedule_scrape_output.json', 'r') as f:
        schedule = json.load(f)
        create_gist(json.dumps(schedule, indent=4))
