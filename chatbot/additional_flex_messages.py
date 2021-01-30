# to get image from a google drive link use:
# https://docs.google.com/uc?id=[id]

def create_image_bubble(ratio, url, animated=False):
    # animated image only supports APNG image (max size: 300KB)
    bubble = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "size": "full",
            "animated": animated,
            "aspectRatio": ratio,
            "aspectMode": "cover",
            "url": url,
            "action": {
                "type": "uri",
                "uri": url
            }
        }
    }
    return bubble


def create_image_carousel(ratio, urls):
    content = []

    for url in urls:
        content.append(create_image_bubble(ratio, url))

    carousel = {
        "type": "carousel",
        "contents": content
    }

    return carousel
