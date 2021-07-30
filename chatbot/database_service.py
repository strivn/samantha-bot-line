import os

from datetime import datetime

import psycopg2
from linebot.models import SourceUser, SourceGroup

from chatbot.calendar_service import timezone

database_url = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(database_url)


def _run_query(connection, query: str, parameters: list = None) -> (bool, list):
    """Runs queries, returns the result, handles exceptions"""

    assert connection is not None, "You need to define connection"

    assert isinstance(query, str), "Query must be in string"

    if parameters is not None:
        assert isinstance(parameters, list), "Parameters must be an iterable"

    query_type = query.split()[0].lower()
    assert query_type in ['select', 'update', 'insert',
                          'delete'], (query_type + " not supported")

    operation_succeed = False
    results = []

    with connection.cursor() as cursor:
        # as this is a generalised function for all kinds of query, we need to
        # define cases when the query does not return anything.
        # example of such case is when doing an update or delete query
        try:
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)

            if query_type == 'select':
                results = cursor.fetchall()

            connection.commit()
            operation_succeed = True
            print("Query completed: {}".format(cursor.query))

        except (psycopg2.errors.SyntaxError, psycopg2.InternalError) as error:
            connection.rollback()
            print("Syntax or Internal Error: {}".format(error))
            print("Query failed: {}".format(cursor.query))

        except psycopg2.Error as other_errors:
            connection.rollback()
            print("Unspecified error: {}".format(other_errors))
            print("Query failed: {}".format(cursor.query))

    return operation_succeed, results


def get_code(item: str) -> str:
    '''
    returns a code based on the item name
    '''

    query = "SELECT code FROM codes WHERE item=%s"
    parameters = [item]

    success, results = _run_query(conn, query, parameters)

    if success:
        return results[0][0]
    else:
        return "Gagal, coba lagi"


def get_command(command_name) -> (int, str, str):
    '''
    get a command's type, content, and clearance based on the command name

    returns (type, content, clearance)
    '''

    query = "SELECT type, content, clearance FROM commands WHERE name=%s"
    parameters = [command_name]

    # ensure that name is the primary key, therefore it will not return
    # multiple commands
    success, results = _run_query(conn, query, parameters)

    if success:
        return results[0]
    else:
        return None


def get_command_description(command_name):
    '''
    get a command's description based on the command name

    returns (description)
    '''

    query = "SELECT description FROM commands WHERE name=%s"
    parameters = [command_name]

    # ensure that name is the primary key, therefore it will not return
    # multiple commands
    success, results = _run_query(conn, query, parameters)

    if success:
        return results[0][0]
    else:
        return "-"


def update_code(item, code):
    '''
    update a code

    currently there are only these items:

    - ruang_alat
    - loker_doksos
    - lemari_oren
    - eneng
    - cici

    '''
    query = "UPDATE codes SET code=%s WHERE item=%s"
    parameters = [code, item]
    success, _ = _run_query(conn, query, parameters)

    return success


def add_follower(user_id, user_name, user_type):
    '''
    add a follower to the database

    parameters ->
    user_id,
    user_name,
    user_type

    user_type is 0 for unregistered, 1 for kru, and 2 for fungsionaris.
    '''
    query = """INSERT INTO followers (user_id, display_name, user_type) VALUES (%s,%s,%s)"""
    parameters = [user_id, user_name, user_type]
    success, _ = _run_query(conn, query, parameters)

    return success


def remove_follower(user_id):
    '''
    remove a follower by user_id 

    parameters ->
    user_id 
    '''

    query = "DELETE FROM followers WHERE user_id=%s"
    parameters = [user_id]
    success, _ = _run_query(conn, query, parameters)

    return success


def add_group(group_id, group_name):
    '''
    register a group to the database, saves the id and name
    group_type will be 0 by default. do change this later by accessing the database directly

    parameters -> 
    group_id,
    group_name

    get these parameters from the user message with !Register
    '''

    cursor = conn.cursor()

    try:
        query = "SELECT * FROM groups WHERE group_id = '{}'".format(
            group_id)
        cursor.execute(query)
        result = cursor.fetchone()
        if (result):
            print("Group is already registered")
            return
        else:
            try:
                group_type = 0
                query = """INSERT INTO groups (group_id, group_name, group_type) VALUES ('{}','{}',{})""".format(
                    group_id, group_name, group_type)
                cursor.execute(query)
                conn.commit()
            except (Exception, psycopg2.Error) as e:
                print("Error in update operation", e)
                print("Error: ", query)
            else:
                print("Query completed : '{}' ".format(query))
    except (Exception, psycopg2.Error) as e:
        print("Error in update operation", e)
        print("Error: ", query)
    else:
        print("Query completed : '{}' ".format(query))
    cursor.close()


def track_api_calls(api_call, user_id):
    now = timezone.localize(datetime.now())
    query = "INSERT INTO api_calls (timestamp, user_id, api_call) VALUES (%s, %s, %s)"
    parameters = [now, user_id, api_call]

    success, _ = _run_query(conn, query, parameters)

    return success


def authenticate(source, num):
    '''
    check whether the source is authenticated against num. 

    num parameters ->
    1 : kru
    2 : fungs

    the source type should be event.source

    returns: bool
    '''
    query = ''

    if isinstance(source, SourceGroup):
        _from = "groups"
        _where = "group_id"
        _type = 'group_type'
        _id = source.group_id
        query = "SELECT * FROM groups WHERE group_id=%s"
    elif isinstance(source, SourceUser):
        _from = "followers"
        _where = "user_id"
        _type = "user_type"
        _id = source.user_id
        query = "SELECT * FROM followers WHERE user_id=%s"
    # currently no support for rooms yet.
    else:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(query, [_id])
        result = cursor.fetchone()
        cursor.close()
        # check if result exists. if it doesn't that means the user is not registered yet.
        if result:
            # check user/group type
            return bool(result[2] >= num)
        else:
            return False

    except (Exception, psycopg2.Error) as e:
        print("Error in update operation", e)
        print("Error: ", cursor.query)
        cursor.close()
