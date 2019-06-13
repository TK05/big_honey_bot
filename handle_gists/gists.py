# TODO: Handle response_code != 201
import json
import os
import requests

from config import gists


USERNAME = os.environ['GISTS_USERNAME']
API_TOKEN = os.environ['GISTS_API']

gists_url = "https://api.github.com/gists"
gists_header = {'X-Github-username': USERNAME, 'Content-Type': 'application/json',
                'Authorization': f"token {API_TOKEN}"}


def update_gist(description, gist_key, paste_data):
    """Updates a Gist.
    Uses gist_key to gather config data from config/config.py.
    Returns gist url for later console logging.
    """

    data = json.dumps({
        "description": f"{description}",
        "public": 'false',
        "files": {
            f"{gists[gist_key]['filename']}": {
                "content": f"{paste_data}"
            }
        }
    })

    response = requests.patch(f"{gists_url}/{gists[gist_key]['id']}", data=data, headers=gists_header).json()
    gist_url = response['html_url']

    return gist_url


def get_gist(gist_key):
    """Return Gist content from given gist_key
    Content is returned as-is (IE: string instead of JSON)
    """

    response = requests.get(f"{gists_url}/{gists[gist_key]['id']}", headers=gists_header)

    response_json = response.json()
    content = response_json['files'][gists[gist_key]['filename']]['content']

    return content
