import os
import requests

from cachetools.func import ttl_cache
from datetime import datetime
from dateutil import parser
import pytz

# google script calendar api
calendar_endpoint = os.environ.get('CALENDAR_ENDPOINT')
calendar_endpoint_token = os.environ.get('CALENDAR_ENDPOINT_TOKEN')

if calendar_endpoint:
    timezone = pytz.timezone("UTC")  # set as UTC as heroku runs on UTC
else:
    # set as Asia/Jakarta on local machine
    timezone = pytz.timezone("Asia/Jakarta")


@ttl_cache(maxsize=2, ttl=600)
def create_lfm_agenda(duration):
    response = requests.get(
        calendar_endpoint + "?key=" + calendar_endpoint_token + "&duration=" + duration)

    content = []
    content.append({
        "type": "text",
        "text": "Agenda LFM",
        "weight": "bold",
        "size": "sm"
    })

    checker = 'Liga Film Mahasiswa ITB 2020/2021'

    if response.json():
        for ev in response.json():
            if ev['cal'] == checker:
                date = parser.parse(ev['start'])

                d = create_date_string(date)

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
                                            "backgroundColor": line_color},
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
                            "text": ev['summary'].replace(" - ", "\n"),
                            "wrap": True,
                            "gravity": "center",
                            "size": "sm",
                            "color": "#444444",
                            "flex": 70
                        }
                    ]
                }
                content.append(e)
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
        content.append(e)

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
def create_fungs_agenda(duration):

    response = requests.get(
        calendar_endpoint + "?key=" + calendar_endpoint_token + "&duration=" + duration)

    content = []
    content.append({
        "type": "text",
        "text": "Agenda LFM",
        "weight": "bold",
        "align": "center",
        "size": "sm"
    })

    checker = 'Liga Film Mahasiswa ITB 2020/2021'

    if response.json():
        for ev in response.json():
            date = parser.parse(ev['start'])

            d = create_date_string(date)

            if ev['cal'] != checker:
                # append separator
                content.append({
                    'type': 'separator',
                    'color': '#CCCCCC',
                    'margin': 'lg'
                })
                # append title
                content.append({
                    "type": "text",
                    "text": "Agenda Fungs",
                    "weight": "bold",
                    "align": "center",
                    "size": "sm"
                })
                checker = ev['cal']

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
                        "text": ev['summary'].replace(" - ", "\n"),
                        "wrap": True,
                        "gravity": "center",
                        "size": "sm",
                        "color": "#444444",
                        "flex": 70
                    }
                ]
            }
            content.append(e)

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
