import json
import logging
from retrying import retry

from gcsa.google_calendar import GoogleCalendar
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from google.auth.exceptions import TransportError

from big_honey_bot.config.helpers import get_env
from big_honey_bot.config.helpers import get_env, get_pname_fname_str


logger = logging.getLogger(get_pname_fname_str(__file__))


def create_service(calendar_id=None, credentials_string=None):
    calendar_id = calendar_id or get_env('GOOGLE_CALENDAR_ID')
    scopes = ['https://www.googleapis.com/auth/calendar']

    # import/read credentials string & clean private key
    credentials_dict = json.loads(credentials_string or get_env('GOOGLE_APPLICATION_CREDENTIALS'))
    credentials_dict['private_key'] = credentials_dict['private_key'].replace('\\n', '\n')

    service_account_creds = service_account.Credentials.from_service_account_info(credentials_dict, scopes=scopes)

    return GoogleCalendar(calendar_id, credentials=service_account_creds)


def retry_calendar_error(exception):
    if isinstance(exception, HttpError):
        # Retry rate limits and transient Google server failures
        should_retry = exception.resp.status in (429, 500, 502, 503, 504)

    elif isinstance(exception, (TransportError, TimeoutError, ConnectionError)):
        # Retry transient network/authentication transport errors
        should_retry = True

    else:
        # Do not retry application errors, JSON parsing, etc.
        should_retry = False

    if should_retry:
        logger.warning(
            "Retrying Google Calendar request after error: %r",
            exception,
        )

    return should_retry


calendar_retry = retry(
    retry_on_exception=retry_calendar_error,
    stop_max_attempt_number=3,
    wait_exponential_multiplier=1000,
    wait_exponential_max=10000,
)
