import os
import json

from collections import Counter
from datetime import datetime, timedelta
from dateutil import parser

import psycopg2
import pytz

from flask import render_template, redirect, request, abort, session, escape

from chatbot.database_service import _run_query
from chatbot.calendar_service import timezone
from chatbot.bot import line_bot_api

DATABASE_URL = os.environ.get('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)


def check_login():
    if 'display_name' in session:
        return True
    return False


def render():
    if check_login():
        # get everything
        api_calls_history = get_all_api_calls()
        # from the data selected, count occurences per day
        timestamp_count = get_api_calls_timestamp_counter(api_calls_history)
        timestamp_values = json.dumps(
            [x-1 for x in list(timestamp_count.values())])
        timestamp_axis = json.dumps(list(timestamp_count.keys()))
        # from the data selected, count occurences per command, take 5 most common
        commands_count = get_api_calls_counter(
            api_calls_history).most_common(5)
        # generate a list of values only, as commands_count produces a list of tuples
        commands_values = json.dumps([t[1] for t in commands_count])
        commands_axis = json.dumps([t[0] for t in commands_count])
        return render_template('dashboard.html', data=api_calls_history, timestamp_values=timestamp_values, timestamp_axis=timestamp_axis, commands_axis=commands_axis, commands_values=commands_values)
    return redirect('/login')


def commands_render():
    if check_login():
        data = get_all_commands()
        return render_template('commands.html', data=data)
    return abort(403)


def render_add_new():
    if check_login():
        return (render_template('commands_new.html'))
    return abort(403)


def render_users():
    if check_login():
        data = get_all_users()
        return (render_template('users.html', data=data))
    return abort(403)


def toggle_clearance(display_name):
    if check_login():
        return toggle_user_clearance(display_name)
    return abort(403)


def update_command(command_name):
    if check_login():

        command_type = request.form['type'].lower()
        command_name = request.form['name'].lower()
        command_description = request.form['description']
        command_clearance = request.form['clearance']

        if command_type == "image":
            command_url = request.form['url']
            command_ratio = request.form['ratio']
            command_alt_text = request.form['alt_text']
            content = {
                "ratio": command_ratio,
                "url": command_url,
                "alt_text": command_alt_text,
            }
            command_content = json.dumps(content)
        elif command_type == 'image carousel':
            command_url = request.form['url']
            command_ratio = request.form['ratio']
            command_alt_text = request.form['alt_text']
            content = {
                "ratio": command_ratio,
                "url": command_url.splitlines(),
                "alt_text": command_alt_text,
            }
            command_content = json.dumps(content)
        elif command_type == 'text':
            command_content = request.form['content']

        query = "UPDATE commands SET type=%s, description=%s, clearance=%s, content=%s WHERE name=%s"
        parameters = [command_type, command_description,
                      command_clearance, command_content, command_name]

        success, _ = _run_query(conn, query, parameters)
        if success:
            return redirect("/commands")
        else:
            abort(500)
    return abort(403)


def edit_command(command_name):
    if check_login():
        query = "SELECT * FROM commands WHERE name=%s"

        success, results = _run_query(conn, query, [command_name])

        if success:
            result = results[0]
            if result:
                if result[3] == 'image':
                    image_data = json.loads(result[1])
                    result = result[0], image_data['url'], result[2], result[3], result[4], image_data['ratio'], image_data['alt_text']
                elif result[3] == 'image carousel':
                    image_data = json.loads(result[1])
                    result = result[0], '\r\n'.join(
                        image_data['url']), result[2], result[3], result[4], image_data['ratio'], image_data['alt_text']
                return render_template('commands_edit.html', data=result)
        else:
            return abort(404)

    return abort(403)


def delete_command(command_name):
    if check_login():

        query = "DELETE FROM commands WHERE name=%s"

        success, _ = _run_query(conn, query, [command_name])

        if success:
            return redirect("/commands")
        else:
            return abort(500)
    return abort(403)


def create_new_command():
    if check_login():
        command_type = request.form['type'].lower()
        command_name = request.form['name'].lower()
        command_description = request.form['description']
        command_clearance = request.form['clearance']

        if command_type == "image":
            command_url = request.form['url']
            command_ratio = request.form['ratio']
            command_alt_text = request.form['alt_text']
            content = {
                "ratio": command_ratio,
                "url": command_url,
                "alt_text": command_alt_text,
            }
            command_content = json.dumps(content)
        elif command_type == 'image carousel':
            command_url = request.form['url']
            command_ratio = request.form['ratio']
            command_alt_text = request.form['alt_text']
            content = {
                "ratio": command_ratio,
                "url": command_url.splitlines(),
                "alt_text": command_alt_text,
            }
            command_content = json.dumps(content)
        elif command_type == 'text':
            command_content = request.form['content']

        query = "INSERT INTO commands (type, name, description, clearance, content) VALUES (%s, %s, %s, %s, %s)"
        parameters = [command_type, command_name,
                      command_description, command_clearance, command_content]

        success, _ = _run_query(conn, query, parameters)

        if success:
            return redirect("/commands")
        else:
            return abort(500)
    return abort(403)


def get_all_api_calls():
    query = "SELECT timestamp, display_name, api_call FROM api_calls JOIN followers ON followers.user_id = api_calls.user_id"

    def format_date(api_call):
        date = parser.parse(api_call[0])
        lst = list(api_call)
        lst[0] = datetime.strftime(date.astimezone(
            pytz.timezone("Asia/Jakarta")), '%a, %d-%m-%Y %H:%M:%S')

        return tuple(lst)

    success, results = _run_query(conn, query)
    results.reverse()

    if success:
        return list(map(format_date, results))


def get_api_calls_timestamp_counter(data, max_days=60):

    if data:
        timestamps = [item[0][5:15] for item in data]  # take only the dates

        # convert to datetime to get the last `max_days` days
        dates = [datetime.strptime(timestamp, '%d-%m-%Y').date()
                 for timestamp in timestamps]
        now = timezone.localize(datetime.now()).date()
        sorted_dates = [date for date in dates if (
            now - date).days <= max_days]

        # add other dates that don't have any occurence
        other_dates = [now - timedelta(days=x) for x in range(max_days)]

        # convert back to string
        date_calls_counter = Counter(
            [d.isoformat() for d in other_dates + sorted_dates])
    else:
        return None

    return date_calls_counter


def get_api_calls_counter(data):

    if data:
        commands_used = [item[2].lower() for item in data]
        api_calls_counter = Counter(commands_used)
    else:
        return None

    return api_calls_counter


def get_all_commands():
    query = "SELECT * FROM commands WHERE type='text' OR type='image' OR type='image carousel'"

    return_data = []
    success, results = _run_query(conn, query)

    if success:
        for result in results:
            if result[3] == 'image' or result[3] == 'image carousel':
                image_data = json.loads(result[1])
                return_data.append(
                    (escape(result[0]), image_data['url'], escape(result[2]), result[3], result[4]))
            elif result[3] == 'text':
                return_data.append(
                    (escape(result[0]), escape(result[1]), escape(result[2]), result[3], result[4]))
        return return_data

    else:
        return abort(500)


def get_all_users():
    query = "SELECT display_name, user_type, picture_url FROM followers"

    success, results = _run_query(conn, query)

    if success:
        return results


def toggle_user_clearance(display_name):

    query = "SELECT user_type FROM followers WHERE display_name=%s"
    parameters = [display_name]

    success, results = _run_query(conn, query, parameters)

    if success:
        result = results[0]
        if result[0] == 1:
            query = "UPDATE followers SET user_type=2 WHERE display_name=%s"
        elif result[0] == 2:
            query = "UPDATE followers SET user_type=1 WHERE display_name=%s"
        success, _ = _run_query(conn, query, parameters)
        if success:
            return "True"
        else:
            return "False"
    else:
        return "False"
