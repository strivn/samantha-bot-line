import os
from datetime import datetime

from bs4 import BeautifulSoup
from bs4.element import Tag
from cachetools.func import ttl_cache

import requests

movie_api_key = os.environ.get('MOVIE_API_KEY')

url_xxi_ciwalk = 'https://21cineplex.com/theater/bioskop-ciwalk-xxi,249,BDGCIWL.htm'
url_cgv_bec = 'https://www.cgv.id/en/schedule/cinema/014'
url_cgv_pvj = 'https://www.cgv.id/en/schedule/cinema/001'


@ttl_cache(maxsize=4, ttl=14400)
def get_now_showing():
    '''Find ongoing movies in several cinemas in Bandung (CGV PVJ, CGV BEC, and XXI Ciwalk).

    Returns a set of movies with title, schedule, and the cinema its playing at.
    '''

    def add_movies_to_now_showing(now_showing, movie_to_be_added, cinema_name):
        '''A nested function to add movies to the now showing list.
        '''
        movie_exists = next(
            (movie for movie in now_showing if movie['title'] == movie_to_be_added['title']), None)

        if movie_exists:
            movie_exists[cinema_name] = movie_to_be_added[cinema_name]
        else:
            now_showing.append(movie_to_be_added)

    def add_cgv_movies(movies_list, cinema_name):
        ''' A nested function add cgv movies to the now showing list. 

        Different function since there is a need to restructure the data separately. (Different format)
        '''
        for i in movies_list:
            if isinstance(i, Tag):
                sched = i.find(class_='showtime-lists')

                movie_to_be_added = {
                    'title': i.div.a.getText().strip().upper(),
                    cinema_name: sched.getText().split()
                }

                add_movies_to_now_showing(
                    now_showing, movie_to_be_added, cinema_name)

    # workaround for ssl error in xxi website
    try:
        xxi_ciwalk = requests.get(url_xxi_ciwalk)
    except:
        xxi_ciwalk = requests.get(url_xxi_ciwalk, verify=False)

    cgv_pvj = requests.get(url_cgv_pvj)
    cgv_bec = requests.get(url_cgv_bec)

    # must add robustness. Currently if there's no movie listed the bot doesnt return anything.

    movies_xxi_ciwalk = BeautifulSoup(xxi_ciwalk.text, 'html.parser')
    movies_cgv_pvj = BeautifulSoup(cgv_pvj.text, 'html.parser')
    movies_cgv_bec = BeautifulSoup(cgv_bec.text, 'html.parser')

    movies_xxi_ciwalk = movies_xxi_ciwalk.find(
        class_='tab-pane fade show active panel-reguler').find_all(class_='col-9')
    movies_cgv_pvj = movies_cgv_pvj.find(class_='schedule-lists').ul
    movies_cgv_bec = movies_cgv_bec.find(class_='schedule-lists').ul

    now_showing = []

    # new website
    for movie in movies_xxi_ciwalk:
        if (movie.h3.text):

            # create a new list to be added later
            schedule_lists = []
            # get showing hours from collected data
            showing_hours = movie.find_all('a')

            # add showing hours to the list
            for hours in showing_hours:
                schedule_lists.append(hours.text)

            movie_to_be_added = {
                'title': movie.h3.text.upper().strip(),
                'Ciwalk XXI': schedule_lists
            }

            add_movies_to_now_showing(
                now_showing, movie_to_be_added, 'Ciwalk XXI')

    add_cgv_movies(movies_cgv_bec, 'CGV BEC')
    add_cgv_movies(movies_cgv_pvj, 'CGV PVJ')

    sorted_now_showing = sorted(now_showing, key=lambda k: k['title'])

    return sorted_now_showing


@ttl_cache(maxsize=4, ttl=3600)
def discover_movies(start_date=None, end_date=None, region='ID'):
    """Find movies based on several parameters. start_date, end_date, and region"""

    # url and default parameter (api key is required)
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        'api_key': movie_api_key,
        'sort_by': 'release_date.asc'
    }
    # additional parameters
    if start_date:
        params['primary_release_date.gte'] = start_date
    if end_date:
        params['primary_release_date.lte'] = end_date
    if region:
        params['region'] = region
    # send request and return response
    response = requests.get(url, params=params)
    return response.json()['results']


@ttl_cache(maxsize=128, ttl=14400)
def get_movie_details(movie_id):
    # url and default parameter (api key and movie id is required)
    url = 'https://api.themoviedb.org/3/movie/{}'.format(movie_id)
    credits_url = 'https://api.themoviedb.org/3/movie/{}/credits'.format(
        movie_id)

    params = {
        'api_key': movie_api_key
    }

    response = requests.get(url, params=params)
    response_credits = requests.get(credits_url, params=params)

    respjson = response.json()

    for key, value in response_credits.json().items():
        respjson[key] = value

    return respjson


def create_now_showing_carousel(movies):

    # initiate variables
    counter = 0
    bubbles = []
    three_movies_section = []
    three_movies_section.append({
        "type": "text",
        "text": datetime.now().strftime('NOW SHOWING\n (%a, %d %b)'),
        "weight": "bold",
        "wrap": True,
        "size": "sm",
        "align": "center"
    })

    length = len(movies)
    length_counter = 0

    for movie in movies:

        length_counter = length_counter + 1
        contents = []

        val_cgv_pvj = movie.get('CGV PVJ')
        val_cgv_bec = movie.get('CGV BEC')
        val_ciwalk_xxi = movie.get('Ciwalk XXI')

        if val_cgv_pvj:
            content = []
            content.append({
                "type": "text",
                "text": "CGV PVJ",
                "wrap": True,
                "gravity": "center",
                "size": "sm",
                "color": "#444444",
                "flex": 2
            })
            content.append({
                "type": "text",
                "wrap": True,
                "gravity": "center",
                "text": ' '.join(val_cgv_pvj),
                "size": "xs",
                "flex": 4
            })

            contents.append({
                "type": "box",
                "layout": "horizontal",
                "contents": content
            })

        if val_cgv_bec:
            content = []
            content.append({
                "type": "text",
                "text": "CGV BEC",
                "wrap": True,
                "gravity": "center",
                "size": "sm",
                "color": "#444444",
                "flex": 2
            })
            content.append({
                "type": "text",
                "wrap": True,
                "gravity": "center",
                "text": ' '.join(val_cgv_bec),
                "size": "xs",
                "flex": 4
            })

            contents.append({
                "type": "box",
                "layout": "horizontal",
                "contents": content
            })

        if val_ciwalk_xxi:
            content = []
            content.append({
                "type": "text",
                "text": "Ciwalk XXI",
                "wrap": True,
                "gravity": "center",
                "size": "sm",
                "color": "#444444",
                "flex": 2
            })
            content.append({
                "type": "text",
                "wrap": True,
                "gravity": "center",
                "text": ' '.join(val_ciwalk_xxi),
                "size": "xs",
                "flex": 4
            })

            contents.append({
                "type": "box",
                "layout": "horizontal",
                "contents": content
            })

        # add the movies

        three_movies_section.append({
            "type": "separator",
        })
        three_movies_section.append({
            "type": "text",
            "text": movie['title'],
            'wrap': True,
            "weight": "bold",
            "size": "sm"
        })

        three_movies_section.append({
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": contents
        })

        # increment counter
        counter = counter + 1

        # if counter has reached 3
        if counter == 3:
            bubbles.append({
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "contents": three_movies_section
                },
            })

            # reset counter
            counter = 0

            # reset three movies section
            three_movies_section = []
            three_movies_section.append({
                "type": "text",
                "text": datetime.now().strftime('NOW SHOWING\n (%a, %d %b)'),
                "weight": "bold",
                "wrap": True,
                "size": "sm",
                "align": "center"
            })
        elif length_counter == length:
            bubbles.append({
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "contents": three_movies_section
                },
            })

    carousel = {
        "type": "carousel",
        "contents": bubbles
    }

    return carousel


def create_upcoming_movies_bubble(movie):
    contents = []
    # add title
    contents.append({
        "type": "text",
        "text": movie['title'],
        "weight": "bold",
        "size": "sm",
        "wrap": True
    })

    contents.append({
        "type": "text",
        "text": datetime.strptime(movie['release_date'], '%Y-%m-%d').strftime('%d %b %Y'),
        "size": "xs"
    })

    bubble = {
        "type": "bubble",
        "hero": {
                "type": "image",
                "size": "full",
                "aspectRatio": "1:1.33",
                "aspectMode": "cover",
                "url": "https://image.tmdb.org/t/p/w500{}".format(movie['poster_path'])
        },
        "body": {
            "type": "box",
            "layout": "horizontal",
            "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "flex": 4,
                    "spacing": "sm",
                    "contents": contents
            },
                {
                "type": "image",
                    "flex": 1,
                    "size": "xxs",
                    "aspectMode": "fit",
                    "url": "https://www.themoviedb.org/assets/2/v4/logos/293x302-powered-by-square-blue-ee05c47ab249273a6f9f1dcafec63daba386ca30544567629deb1809395d8516.png"
            }]
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [{
                "type": "spacer",
                "size": "md"
            }, {
                "type": "button",
                "height": "sm",
                # "action": {
                #         "type": "postback",
                #         "label": "Details..",
                #         "data": "{}".format(str(movie['id'])),
                # },
                "action": {
                        "type": "uri",
                        "label": "Details..",
                        "uri": "https://www.themoviedb.org/movie/{}".format(str(movie['id'])),
                },
                "style": "secondary",
                "color": "#F1F1F1",
                "flex": 2
            }]
        }
    }

    return bubble


def create_movie_details_bubble(movie):
    contents = []
    # add title
    contents.append({
        "type": "text",
        "text": movie['title'],
        "weight": "bold",
        "size": "sm",
        "wrap": True
    })

    if movie['runtime']:
        contents.append({
            "type": "text",
            "text": "{} minutes ".format(movie['runtime']),
            "size": "xs"
        })

    # add crew information
    if movie['crew']:
        directors = []
        screenplays = []

        for person in movie['crew']:
            if (person['job'] == 'Director'):
                directors.append(person['name'])
            elif (person['job'] == 'Script' or person['job'] == 'Writer' or person['job'] == 'Screenplay'):
                screenplays.append(person['name'])

        # Add the directors
        if (directors):
            crew_contents = []
            crew_contents.append({
                "type": "text",
                "wrap": True,
                "text": "Director:",
                "flex": 1,
                "size": "xxs"
            })
            crew_contents.append({
                "type": "text",
                "text": ', '.join(directors),
                "wrap": True,
                "flex": 3,
                "size": "xxs",
                "weight": "bold"
            })
            contents.append({
                "type": "box",
                "spacing": "xs",
                "layout": "horizontal",
                "contents": crew_contents
            })

        # Add the screenwriters
        if (screenplays):
            crew_contents = []
            crew_contents.append({
                "type": "text",
                "wrap": True,
                "flex": 1,
                "text": "Script: ",
                "size": "xxs"
            })
            crew_contents.append({
                "type": "text",
                "text": ', '.join(screenplays),
                "wrap": True,
                "flex": 3,
                "size": "xxs",
                "weight": "bold"
            })

            contents.append({
                "type": "box",
                "spacing": "xs",
                "layout": "horizontal",
                "contents": crew_contents
            })

    # add movie description
    if (movie['overview']):
        contents.append({
            "type": "text",
            "wrap": True,
            "text": movie['overview'],
            "size": "xs"
        })
    else:
        contents.append({
            "type": "text",
            "wrap": True,
            "text": "-",
            "size": "xs"
        })
    # add movie website
    if (movie['homepage']):
        contents.append({
            "type": "text",
            "text": "{}".format(movie['homepage']),
            "size": "xxs",
        })

    bubble = {
        "type": "bubble",
        "hero": {
                "type": "image",
                "size": "full",
                "aspectRatio": "1:1.33",
                "aspectMode": "cover",
                "url": "https://image.tmdb.org/t/p/w500{}".format(movie['poster_path'])
        },
        "body": {
            "type": "box",
            "layout": "horizontal",
            "contents": [{
                    "type": "box",
                    "layout": "vertical",
                    "flex": 4,
                    "spacing": "sm",
                    "contents": contents
            },
                {
                "type": "image",
                    "flex": 1,
                    "size": "xxs",
                    "aspectMode": "fit",
                    "url": "https://www.themoviedb.org/assets/2/v4/logos/293x302-powered-by-square-blue-ee05c47ab249273a6f9f1dcafec63daba386ca30544567629deb1809395d8516.png"
            }]
        },
    }

    return bubble


def create_upcoming_movies_carousel(movies):
    bubbles = []

    # create a counter to make sure it does not exceed 10 bubbles
    counter = 0
    for movie in movies:
        if counter < 10:
            bubbles.append(create_upcoming_movies_bubble(movie))
        else:
            break
        counter = counter + 1

    carousel = {
        "type": "carousel",
        "contents": bubbles
    }

    return carousel

    # -- legacy -- (old website 21)

    # movies_xxi_ciwalk = movies_xxi_ciwalk.find('table', class_='table-theater-det')

    # for i in movies_xxi_ciwalk.find_all('tr'):
    #     if ((i.a) and (i.div)):
    #         movie = {
    #             'title': i.a.next_sibling.getText(),
    #             'Ciwalk XXI': i.div.getText().split()
    #         }
    #         if not (now_showing_reference.get(movie['title'])):
    #             now_showing.append(movie)
    #             now_showing_reference[movie['title']] = counter
    #             counter = counter + 1
    #         else:
    #             now_showing[now_showing_reference.get(
    #                 movie['title'])-1]['Ciwalk XXI'] = movie['Ciwalk XXI']
