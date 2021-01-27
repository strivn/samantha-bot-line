import os
import json

from flask import request, abort

from linebot import (
    LineBotApi, WebhookHandler
)

from linebot.models import (
    MessageEvent, FollowEvent, UnfollowEvent, JoinEvent, PostbackEvent,
    TextMessage, TextSendMessage, FlexSendMessage, StickerSendMessage,
    SourceRoom, SourceGroup
)

from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)

from .additional_flex_messages import whats_sop_kru, create_image_bubble, create_image_carousel
from .calendar_service import create_fungs_agenda, create_lfm_agenda

from .database_service import (
    authenticate, add_follower, add_group,
    get_code, get_command, get_command_description,
    remove_follower, track_api_calls, update_code
)
from .movie_service import (
    create_upcoming_movies_carousel, discover_movies,
    create_now_showing_carousel, get_now_showing,
    get_movie_details, create_movie_details_bubble
)

from .utils import parse_upcoming_movies_params, translate_date_to_words, translate_words_to_date


# line messaging api
channel_access_token = os.environ.get('CHANNEL_ACCESS_TOKEN')
channel_secret = os.environ.get('CHANNEL_SECRET')

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

lfm_muda_beo_id = os.environ.get('ID_LFM_MUDA_BEO')


def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    print(body)
    # app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


def execute_command(event, text_string):

    # separate command string and other parameters or unnecessary inputs
    split_text = text_string.split()

    # get the first word (the command) while
    # lowering the characters and removing the '?' prefix
    command_string = split_text[0].lower()[1:]

    # get other words other than the command itself
    if len(split_text) > 1:
        other_string = split_text[1:]
    else:  # temporary fix
        other_string = []

    # get the command from database
    command_tuple = get_command(command_string)
    # if the command exists in the database, it should be truthy
    if command_tuple:
        # unpack the tuple
        c_type, c_content, c_clearance = get_command(command_string)

        # check if the user has clearance for the command
        if authenticate(event.source, c_clearance):

            # collect data
            track_api_calls(command_string, event.source.user_id)

            # for simple text-based replies
            if c_type == 'text':
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=c_content))

            # for simple image-based replies
            elif c_type == 'image':
                # unpack the content first into ratio and image url
                ratio, image_url, alt_text = json.loads(c_content).values()
                # then create the content bubble using ratio and image url
                content = create_image_bubble(ratio, image_url)
                line_bot_api.reply_message(event.reply_token, FlexSendMessage(
                    alt_text=alt_text, contents=content))

            # for code text-based replies
            elif c_type == 'code':
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=get_code(c_content)))

            # for updating code commands
            elif c_type == 'update_code':
                if other_string:
                    if command_string in ('gantikoderulat', 'gantikodelokerdoksos', 'gantikodelemarioren'):
                        update_code(c_content, other_string[0])
                    else:
                        update_code(c_content, ' '.join(other_string))

                    line_bot_api.reply_message(event.reply_token, TextSendMessage(
                        text=("Kode sudah diganti menjadi " + get_code(c_content))))
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(
                        text=('Mau diganti sama apa kodenya?')))

            elif c_type == 'image carousel':
                # unpack the content first into ratio and image url
                ratio, image_urls, alt_text = json.loads(c_content).values()
                # then create the content bubble using ratio and image url
                content = create_image_carousel(ratio, image_urls)
                line_bot_api.reply_message(event.reply_token, FlexSendMessage(
                    alt_text=alt_text, contents=content))

            # for complex replies [to do list], not yet added to database
            elif c_type == 'others':
                if command_string == 'agenda':
                    duration = translate_words_to_date(' '.join(other_string))
                    alt_text = "Agenda " + \
                        translate_date_to_words(int(duration)) + " Kedepan"
                    if authenticate(event.source, 2):
                        line_bot_api.reply_message(event.reply_token, FlexSendMessage(
                            alt_text=alt_text, contents=create_fungs_agenda(str(duration))))
                    else:
                        line_bot_api.reply_message(event.reply_token, FlexSendMessage(
                            alt_text=alt_text, contents=create_lfm_agenda(str(duration))))
                elif command_string == 'upcomingmovies':
                    start_date, end_date, region = parse_upcoming_movies_params(other_string)
                    line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="Upcoming Movies", contents=create_upcoming_movies_carousel(
                        discover_movies(start_date=start_date, end_date=end_date, region=region))))
                elif command_string == 'nowshowing':
                    line_bot_api.reply_message(event.reply_token, FlexSendMessage(
                        alt_text="Now Showing", contents=create_now_showing_carousel(get_now_showing())))
                elif command_string == 'whatsopkru':
                    line_bot_api.reply_message(event.reply_token, [FlexSendMessage(alt_text="What SOP' Kroe!", contents=whats_sop_kru(
                        1)), FlexSendMessage(alt_text="What SOP' Kroe!", contents=whats_sop_kru(2))])

            elif c_type == 'help':

                # if user asks for detailed help of a command
                if other_string:
                    reply = get_command_description(other_string[0])
                # general help
                else:
                    # commands available for kru
                    commands = '\n  • ?Agenda \n  • ?NowShowing \n  • ?UpcomingMovies \n  • ?Database \n  • ?KodeLemariOren \n  • ?FTP \n  • ?Surat \n  • ?FAQSurat \n  • ?TrackRecord \n  • ?LinkKinekuniya \n  • ?WhatSOPKru \n  • ?Netflix \n  • ?KitMakingMovies \n  • ?Alkhazini \n  • ?PinjamDisney+ \n  • ?YukSukacita'
                    # commands available only for fungs
                    if authenticate(event.source, 2):
                        commands += '\n\n  • ?KodeRulat \n  • ?GantiKodeRulat \n  • ?KodeLokerDoksos \n  • ?GantiKodeLokerDoksos \n  • ?PasswordEneng \n  • ?GantiPasswordEneng \n  • ?PasswordCici \n  • ?GantiPasswordCici'

                    reply = "Halo! \nAku bisa bantu kru sekalian dengan beberapa perintah, diantaranya: " + commands + \
                        "\n\nKalau masih bingung perintahnya untuk apa, coba ketik ?Help dan nama perintahnya, \nmisal: ?Help Agenda "

                # send the message
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text=reply))


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text

    if text[0] == '?':
        if text.split()[0] == "?Register":
            if isinstance(event.source, SourceGroup):
                print(event.source.group_id, ' '.join(text.split()[1:]))
                add_group(event.source.group_id, ' '.join(text.split()[1:]))

        execute_command(event, text)


@handler.add(FollowEvent)
def handle_follow(event):
    # get profile
    profile = line_bot_api.get_profile(event.source.user_id)

    # check if user exists in Muda Beo (change readme to muda beo id later on)
    try:
        line_bot_api.get_group_member_profile(
            lfm_muda_beo_id, event.source.user_id)
        user_type = 1
    except LineBotApiError as err:
        print(err.error.message)
        user_type = 0

    # add said profile to database
    add_follower(profile.user_id, profile.display_name, user_type)

    if user_type == 0:
        welcome_reply = 'Halo, {}! Kenalkan aku Samantha, bot untuk membantu kru LFM. Kalau penasaran aku bisa membantu apa saja, kirim aja \n`?Help`'.format(
            profile.display_name)
        onboarding_reply = 'Oh iya, coba dulu yuk kirim `?Agenda` atau `?NowShowing`, atau pencet aja menu yang udah disediain!'
        privacy_notice = "Omong-omong, aku akan merekam kapan dan fitur apa yang kalian gunakan ya. Kalau kalian tidak mau, karena belum ada sistem untuk opt-out, berkabar saja supaya rekamannya dihapus."
        all_reply = [TextSendMessage(text=welcome_reply),
                     StickerSendMessage(package_id='11537',
                                        sticker_id='52002734'),
                     TextSendMessage(text=onboarding_reply),
                     TextSendMessage(text=privacy_notice)]
    elif user_type == 1:
        welcome_reply = 'Halo, {}! Kenalkan aku Samantha, bot untuk membantu kru LFM. Tampaknya kamu tidak ada di Muda Beo. Maaf, aku tidak bisa membantumu.'.format(
            profile.display_name)
        all_reply = [TextSendMessage(text=welcome_reply)]

    # send a welcoming message and onboarding
    line_bot_api.reply_message(event.reply_token, all_reply)


@handler.add(JoinEvent)
def handle_join(event):
    # get group id
    if isinstance(event.source, SourceGroup):
        reply = "Halo kru! Aku perlu catat nama grupnya dulu nih, tolong kirim ?Register dan nama grupnya. Contoh: ?Register LFM Muda Beo. Terus kalau udah, kabarin ke Ivan yaa. \nTerimakasih!"
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(
            reply), StickerSendMessage(package_id='11537', sticker_id='52002739')])
    if isinstance(event.source, SourceRoom):
        reply = "Halo! Maaf belum bisa bantu di multichat nih. Hehe"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(reply))
        line_bot_api.leave_room(event.source.room_id)


@handler.add(UnfollowEvent)
def handle_unfollow(event):
    remove_follower(event.source.user_id)


@handler.add(PostbackEvent)
def handle_postback(event):
    movie_id = int(event.postback.data)
    line_bot_api.reply_message(event.reply_token, FlexSendMessage(
        alt_text="Movie Details", contents=create_movie_details_bubble(get_movie_details(movie_id))))
