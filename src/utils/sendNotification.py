import requests
import logging


def send_push_notification(expoPushToken: str, title: str, body: str, data: dict = {}, sound: str = 'default') -> None:
    message: dict = {
        "to": expoPushToken,
        "sound": sound,
        "title": title,
        "body": body,
        "data": data
    }

    headers: dict = {
        "host": "exp.host",
        "Accept": "application/json",
        'Accept-encoding': 'gzip, deflate',
        'Content-Type': 'application/json'
    }

    r = requests.post('https://exp.host/--/api/v2/push/send',
                      json=message, headers=headers)

    if r.ok:
        logging.debug("notification sent to, ", expoPushToken)
