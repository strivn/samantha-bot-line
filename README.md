# samantha-bot-line

![](https://docs.google.com/uc?id=1TV18a2T0JhzVt9RVdQacJ8Ci1-6_iSqq)

Samantha is a basic keyword recognition chatbot built with the purpose of providing additional information that LFM members may need. The bot is built on Python and use Bahasa Indonesia as its main language.

There are two main components:

- Chatbot
- Configuration Website

The chatbot component handles requests made to the LINE registered webhook. Meanwhile, the configuration website is intended for users (LFM functionaries) to configure the chatbot replies, see which commands are being used, etc.

The chatbot has features connected to Google Calendar and The Movie Database (TMDb), namely Agenda and Movies. Agenda shows upcoming events from registered Google Calendar (but it is not yet part of this repository), while Movies shows Upcoming Movies. There's also another Movies-related feature, NowShowing, which scraps movies that are currently playing data from cinemas around ITB (Bandung Institute of Technology).

The rest are simple text-based replies and image-based replies that may be modified through the website. 