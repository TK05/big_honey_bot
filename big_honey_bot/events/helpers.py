import json

from gcsa.google_calendar import GoogleCalendar
from google.oauth2 import service_account

from big_honey_bot.config.helpers import get_env


async def create_service(calendar_id=None, credentials_string=None):
    calendar_id = calendar_id or get_env('GOOGLE_CALENDAR_ID')
    scopes = ['https://www.googleapis.com/auth/calendar']

    # import/read credentials string & clean private key
    credentials_dict = json.loads(credentials_string or get_env('GOOGLE_APPLICATION_CREDENTIALS'))
    credentials_dict['private_key'] = credentials_dict['private_key'].replace('\\n', '\n')

    service_account_creds = service_account.Credentials.from_service_account_info(credentials_dict, scopes=scopes)

    return GoogleCalendar(calendar_id, credentials=service_account_creds)
