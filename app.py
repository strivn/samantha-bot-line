import os

from flask import Flask

from chatbot import bot

from frontend import dashboard
from frontend import login

# from apscheduler.schedulers.background import BackgroundScheduler

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


# @app.route('/rollback')
# def _rollback():
#     rollback()
#     return redirect('/')

# @app.route('/', methods=['POST'])
# def index_post():
#     text = request.form['text']
#     line_bot_api.push_message(
#         'C87666fbdcd9256ed17e44ba4335579c5', TextSendMessage(text=text))
#     return redirect('/')


# sched = BackgroundScheduler(timezone="Asia/Jakarta")

# Per 14 March 2020: Turn off sopsor_reminder

# @sched.scheduled_job('cron', day_of_week='*', hour=16, minute=48, misfire_grace_time=180)
# def sopsor_reminder():

#     now = timezone.localize(datetime.now())
#     then = timezone.localize(datetime(2020, 3, 14))
#     date_diff = (then - now).days

#     reminder = [
#         "Sebentar lagi jam 5 nih! Yuk bersih-bersih. Jangan lupa udah tinggal {} hari lagi sebelum kongres!",
#         "Mau ngingetin udah mau jam 5 nih! Yuk bersih-bersih. Maksimalin juga kinerja kalian karna tinggal {} hari lagi sebelum kongres",
#         "Waktunya bersih-bersih rutin! Yuk siap-siap! Ei jangan lupa tinggal {} hari lagi lho sebelum kalian kongres",
#         "Whoa tinggal {} hari lagi sebelum kongres. Ayo berikan yang terbaik! Jangan lupa juga bentar lagi SOPSOR. Ayo sapu ayo lap ayo beberess",
#         "Countdown: H-{} to Kongres. 12 Minutes to SOPSOR"
#     ]

#     line_bot_api.push_message(
#         'C87666fbdcd9256ed17e44ba4335579c5', TextSendMessage(random.SystemRandom().choice(reminder).format(date_diff)))


# @sched.scheduled_job('cron', day_of_week='*', hour=0, minute=0, misfire_grace_time=180)
# def refresh_features_caches():
#     create_fungs_agenda()
#     create_lfm_agenda()
#     get_now_showing()
#     discover_movies()


# sched.start()


if __name__ == "__main__":
    app.run(use_reloader=False)
