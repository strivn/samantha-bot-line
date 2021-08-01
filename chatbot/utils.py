from datetime import datetime, timedelta

import pytz

timezone = pytz.timezone("Asia/Jakarta")

def compose_help_message(commands, authenticated):
    '''
    Compose the help message
    '''
    
    content = ''.join(['\n  • ?{} '.format(command[0]) for command in commands if command[1] == 1])

    if authenticated:
        content += '\n\nDan ini beberapa perintah khusus untuk fungsionaris:'
        content += ''.join(['\n  • ?{} '.format(command[0]) for command in commands if command[1] == 2])

    reply = "Halo! \nAku bisa bantu kru sekalian dengan beberapa perintah, diantaranya: " + content + \
            "\n\nKalau masih bingung perintahnya untuk apa, coba ketik ?Help dan nama perintahnya, \nmisal: ?Help Agenda "

    return reply
    

def parse_upcoming_movies_params(text):
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

    if "us" in text:
        region = 'US'
    elif "jp" in text:
        region = 'JP'
    elif "uk" in text:
        region = 'UK'
    elif "fr" in text:
        region = 'FR'
    else: # defaults to Indonesia
        region = 'ID'

    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d')

    return start_date, end_date, region


def translate_words_to_date(text):
    if ("bulan" in text and "depan" in text):
        duration = 30
    elif ("minggu" in text and "ini" in text):
        duration = 7
    elif text.isdigit():
        duration = int(text)
    # default condition, return a week (7 days)
    else:
        duration = 7

    return duration


def translate_date_to_words(days):
    if days == 7:
        return_value = 'Seminggu'
    elif days in (30, 31):
        return_value = 'Sebulan'
    else:
        return_value = str(days) + ' Hari'

    return return_value
