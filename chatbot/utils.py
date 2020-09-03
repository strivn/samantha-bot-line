from datetime import datetime, timedelta

import pytz

timezone = pytz.timezone("Asia/Jakarta")


def get_dates(text):
    now = timezone.localize(datetime.now())
    text = [word.lower() for word in text]
    # default: bulan ini
    if ("bulan" in text and "depan" in text):
        start_date = now + timedelta(days=+30)
        end_date = start_date + timedelta(days=+30)
    elif ("minggu" in text and "ini" in text):
        start_date = now
        end_date = start_date + timedelta(days=+7)
    elif ("minggu" in text and "depan" in text):
        start_date = now + timedelta(days=+7)
        end_date = start_date + timedelta(days=+7)
    else:
        start_date = now
        end_date = start_date + timedelta(days=+30)
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d')

    return start_date, end_date


def translate_words_to_date(text):
    if ("bulan" in text and "depan" in text):
        duration = 30
    elif ("minggu" in text and "ini" in text):
        duration = 7
    elif (text.isdigit()):
        duration = text
    # default condition, return a week (7 days)
    else:
        duration = 7

    return str(duration)


def translate_date_to_words(days):
    if days == 7:
        return_value = 'Seminggu'
    elif days == 30 or days == 31:
        return_value = 'Sebulan'
    else:
        return_value = str(days) + ' Hari'

    return return_value
