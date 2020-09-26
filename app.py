import os

from flask import Flask

from chatbot import bot

from frontend import dashboard
from frontend import login

app = Flask(__name__, template_folder='./frontend/templates',
            static_folder='./frontend/static')

app.secret_key = os.environ.get('SECRET_KEY')


app.add_url_rule('/', view_func=dashboard.render)

# auth
app.add_url_rule('/login', view_func=login.redirect_login)
app.add_url_rule('/login/callback', view_func=login.login_callback)

# bot
app.add_url_rule('/callback', view_func=bot.callback, methods=['POST'])

# users
app.add_url_rule('/users', view_func=dashboard.render_users, methods=['GET'])
app.add_url_rule('/users/<display_name>', view_func=dashboard.toggle_clearance, methods=['POST'])

# commands
app.add_url_rule(
    '/commands', view_func=dashboard.commands_render, methods=['GET'])
app.add_url_rule(
    '/commands', view_func=dashboard.create_new_command, methods=['POST'])
app.add_url_rule(
    '/commands/new', view_func=dashboard.render_add_new, methods=['GET'])
app.add_url_rule('/commands/<command_name>',
                 view_func=dashboard.edit_command, methods=['GET'])
app.add_url_rule('/commands/<command_name>',
                 view_func=dashboard.update_command, methods=['POST'])

# do change this one later! ---
app.add_url_rule('/commands/delete/<command_name>',
                 view_func=dashboard.delete_command)
# -----

if __name__ == "__main__":
    app.run(use_reloader=False)
