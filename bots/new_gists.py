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
    """Updates a GitHub Gist."""

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
