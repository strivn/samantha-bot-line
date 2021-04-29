import os
import json

from datetime import datetime, timedelta
from dateutil import parser

import pytz

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from cachetools.func import ttl_cache

# google script calendar api,
# i think this is needed as timezone is imported to other services.
# should be updated later
calendar_endpoint = os.environ.get('CALENDAR_ENDPOINT')
calendar_endpoint_token = os.environ.get('CALENDAR_ENDPOINT_TOKEN')

# get calendar id
lfm_calendar_id = os.environ.get('LFM_CALENDAR_ID')
fungs_calendar_id = os.environ.get('FUNGS_CALENDAR_ID')

# google cloud api
raw_credentials = os.environ.get('GSERVICE_ACCOUNT_CREDENTIALS')
json_credentials = json.loads(raw_credentials, strict=False)
credentials = service_account.Credentials.from_service_account_info(
    json_credentials)

# need to check best practice whether create once or create when needed and close afterwards.
service = build('calendar', 'v3', credentials=credentials)

if calendar_endpoint:
    timezone = pytz.timezone("UTC")  # set as UTC as heroku runs on UTC
else:
    # set as Asia/Jakarta on local machine
    timezone = pytz.timezone("Asia/Jakarta")


def get_calendar_metadata(calendar_id):

    # documentation https://developers.google.com/calendar/v3/reference/calendars
    try:
        metadata = service.calendars().get(calendarId=calendar_id).execute()
    except HttpError as err:
        print(err.error_details)
        return None
    return metadata


def create_event_line(event):
    '''
    '''

    if event:

        start = event['start'].get('dateTime', event['start'].get('date'))
        event_start_date = parser.parse(start)

        event_summary = event['summary']

        # some string formatting
        d = create_date_string(event_start_date)

        # set different color for indicating urgency / the event is coming
        line_color = "#AAAAAA"
        if "Today" in d:
            line_color = "#DD3333"
        elif "Tomorrow" in d:
            line_color = "#6486E3"

        e = {
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": d,
                    "wrap": True,
                    "color": "#999999",
                    "gravity": "center",
                    "size": "xxs",
                    "flex": 22
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "filler"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {
                                            "type": "filler"
                                        }
                                    ],
                                    "width": "2px",
                                    "backgroundColor": line_color
                                },
                                {
                                    "type": "filler"
                                }
                            ],
                            "flex": 8
                        }
                    ],
                    "width": "6px"
                },
                {
                    "type": "text",
                    "text": event_summary.replace(" - ", "\n"),
                    "wrap": True,
                    "gravity": "center",
                    "size": "sm",
                    "color": "#444444",
                    "flex": 70
                }
            ]
        }

    else:
        e = {
            "type": "box",
            "layout": "baseline",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": "Tidak ada proker seminggu kedepan",
                    "wrap": True,
                    "size": "sm",
                    "color": "#444444"
                }
            ]
        }
    return e


def request_events(calendar_id, duration):


    now = datetime.utcnow()
    then = (now + timedelta(days=duration))

    time_min = now.isoformat() + 'Z'
    time_max = then.isoformat() + 'Z'

    # documentation: https://developers.google.com/calendar/v3/reference/events/list

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])
    except HttpError as err:
        print(err.error_details)
        return None

    return events


@ttl_cache(maxsize=2, ttl=600)
def create_lfm_agenda(duration=7):

    # get events
    events = request_events(lfm_calendar_id, duration)

    # create agenda header
    header = {
        "type": "text",
        "text": "Agenda LFM",
        "weight": "bold",
        "size": "sm"
    }

    # create content
    content = []
    content.append(header)

    # new (using gcp api)
    if events:
        for event in events:
            content.append(create_event_line(event))
    else:
        content.append(create_event_line(None))
    # end of new

    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": content
        },
    }

    return bubble


@ttl_cache(maxsize=2, ttl=7200)
def create_fungs_agenda(duration=7):

    # get events
    events = request_events(lfm_calendar_id, duration)
    events_fungs = request_events(fungs_calendar_id, duration)

    # create agenda header
    header = {
        "type": "text",
        "text": "Agenda LFM",
        "weight": "bold",
        "align": "center",
        "size": "sm"
    }

    # create content
    content = []
    content.append(header)

    # new (using gcp api)
    if events:
        for event in events:
            content.append(create_event_line(event))
    else:
        content.append(create_event_line(None))

    # add separator
    content.append({
        'type': 'separator',
        'color': '#CCCCCC',
        'margin': 'lg'
    })
    content.append({
        "type": "text",
        "text": "Agenda Fungs",
        "weight": "bold",
        "align": "center",
        "size": "sm"
    })

    if events_fungs:
        for event in events:
            content.append(create_event_line(event))
    else:
        content.append(create_event_line(None))

    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": content
        },
    }
    return bubble


def create_date_string(date):
    '''create date string for bot with format:

    "date"
    "hour:min"

    parameter required is a parsed datetime format.'''
    d = ""
    # add date
    now = timezone.localize(datetime.now())
    if (date.date() - now.date()).days <= 0:
        d = "Today"
    elif (date.date() - now.date()).days == 1:
        d = "Tomorrow"
    else:
        d = "{}".format(date.strftime('%a')) + \
            "\n{}".format(date.strftime('%d %b'))

    # add time
    if (date.hour or date.minute):
        d += "\n{}".format(date.strftime('%H:%M'))

    return d
