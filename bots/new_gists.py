import json
import os
import requests


USERNAME = os.environ['GISTS_USERNAME']
API_TOKEN = os.environ['GISTS_API']

gists_files = {'pre': [os.environ['GISTS_PRE_FN'], os.environ['GISTS_PRE_ID']],
               'game': [os.environ['GISTS_GAME_FN'], os.environ['GISTS_GAME_ID']],
               'post': [os.environ['GISTS_POST_FN'], os.environ['GISTS_POST_ID']]}

gists_url = "https://api.github.com/gists"
gists_header = {'X-Github-username': USERNAME, 'Content-Type': 'application/json',
                'Authorization': f"token {API_TOKEN}"}


def update_gist(description, thr_type, paste_data):

    data = json.dumps({
        "description": f"{description}",
        "public": 'false',
        "files": {
            f"{gists_files[thr_type][0]}": {
                "content": f"{paste_data}"
            }
        }
    })

    response = requests.patch(f"{gists_url}/{gists_files[thr_type][1]}", data=data, headers=gists_header).json()
    gist_url = response['html_url']

    return gist_url
