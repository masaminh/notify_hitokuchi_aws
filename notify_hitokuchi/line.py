"""LINEへのアクセス関数群."""
import logging

import requests
from retry import retry


def notify(token, message):
    """LINE Notifyでメッセージを送る."""
    payload = {'message': message}
    headers = {'Authorization': 'Bearer ' + token}
    res = _call_notify_api(payload, headers)
    logging.info('LINE Notify response status code: %d', res.status_code)
    logging.info('LINE Notify response: %s', res.text)


@retry(requests.exceptions.RequestException, tries=2, delay=10)
def _call_notify_api(payload, headers):
    res = requests.post('https://notify-api.line.me/api/notify',
                        data=payload, headers=headers)
    if res.status_code > 500:
        res.raise_for_status()

    return res
