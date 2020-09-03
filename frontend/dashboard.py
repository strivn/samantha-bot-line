import os
import json

from datetime import datetime
from dateutil import parser

import psycopg2
import pytz

from flask import render_template, redirect, request, abort, session

from chatbot.database_service import _run_query

DATABASE_URL = os.environ.get('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)


def check_login():
    if 'display_name' in session:
        return True
    return False


def render():
    if check_login():
        data = get_all_api_calls()
        return render_template('dashboard.html', data=data)
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
        else:
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
                    result = result[0], image_data['url'], result[2], result[3], result[4], image_data['ratio'], image_data['alt_text'],
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
        else:
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


def get_all_commands():
    query = "SELECT * FROM commands WHERE type='text' OR type='image'"

    return_data = []
    success, results = _run_query(conn, query)

    if success:
        for result in results:
            if result[3] == 'image':
                image_data = json.loads(result[1])
                return_data.append(
                    (result[0], image_data['url'], result[2], result[3], result[4]))
            else:
                return_data.append(
                    (result[0], result[1], result[2], result[3], result[4]))
        return return_data

    else:
        return abort(500)


def get_all_users():
    query = "SELECT display_name, user_type FROM followers"

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
