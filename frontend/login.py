import os
import json
import secrets
from urllib.parse import urlencode

import requests
import jwt
import psycopg2
from flask import redirect, request, abort, session

DATABASE_URL = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)

CHANNEL_ID = os.environ.get('CHANNEL_LOGIN_ID')
CHANNEL_SECRET = os.environ.get('CHANNEL_LOGIN_SECRET')
REDIRECT_URI = 'https://samantha-bot-line.herokuapp.com/login/callback'


def redirect_login():
    base_url = 'https://access.line.me/oauth2/v2.1/authorize'
    state_token = secrets.token_urlsafe()
    parameters = {
        'response_type': 'code',
        'client_id': CHANNEL_ID,
        'redirect_uri': REDIRECT_URI,
        'state': state_token,
        'scope': 'profile openid',
        'bot_prompt': 'normal',
    }
    url = base_url + '?' + urlencode(parameters)

    return redirect(url)


def login_callback():

    # check whether the client returns error code or valid token code
    try:
        request_code = request.args['code']
    except KeyError:
        return

    base_url = 'https://api.line.me/oauth2/v2.1/token'

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data_params = {
        "grant_type": "authorization_code",
        "code": request_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CHANNEL_ID,
        "client_secret": CHANNEL_SECRET
    }

    response_post = requests.post(base_url, headers=headers, data=data_params)

    id_token = json.loads(response_post.text)['id_token']

    decoded_id_token = jwt.decode(id_token,
                                  CHANNEL_SECRET,
                                  audience=CHANNEL_ID,
                                  issuer='https://access.line.me',
                                  algorithms=['HS256'])

    # create a profile dictionary
    user_profile = {
        'user_id': decoded_id_token['sub'],
        'display_name': decoded_id_token['name'],
    }

    if front_authenticate(user_profile, 2):
        session['display_name'] = user_profile['display_name']
        return redirect('/')
    return abort(403)


def front_authenticate(profile, num):
    cursor = conn.cursor()
    parameters = [profile['user_id']]
    query = "SELECT * FROM followers WHERE user_id=%s"
    try:
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        result = cursor.fetchone()
        cursor.close()

        # check if result exists. if it doesn't that means the user is not registered yet.
        if result:
            # check user/group type
            return bool(result[2] >= num)
        return False

    except (Exception, psycopg2.Error) as e:
        print("Error in update operation", e)
        print("Error: ", query)
