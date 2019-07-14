"""友駿出走馬の情報通知."""
import logging
import time
from datetime import datetime, timedelta, timezone

import line
import settings
import yushun

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Lambda handler.

    Arguments:
        event {dict} -- Event data
        context {object} -- Lambda Context runtime methods and attributes

    """
    del context

    logger.info('start: event.time=%s', event["time"])

    today = get_jstdate_from_isoformat(event['time'])

    for horseid in settings.YUSHUN_HORSE_ID.split(';'):
        status = yushun.get_horse_latest_status(today, horseid)
        logger.info(
            'latest_status: horseid=%s, status_date=%s',
            horseid, status['status_date'])

        if status['status_date'] == today:
            message = format_status(status)
            line.notify(settings.LINE_NOTIFY_ACCESS_TOKEN, message)

        time.sleep(1)

    return 'OK'


def get_jstdate_from_isoformat(isostr):
    """iso8601文字列からJSTの日付を取得する.

    Arguments:
        isostr {str} -- iso8601

    Returns:
        date -- JSTでの日付

    """
    date_str = isostr.replace('Z', '+00:00')
    date_utc = datetime.fromisoformat(date_str)
    timezone_jst = timezone(timedelta(hours=9))
    date_jst = date_utc.astimezone(timezone_jst).date()
    return date_jst


def format_status(status):
    """状況を文字列整形する.

    Arguments:
        status {dict} -- 状況

    Returns:
        str -- 整形後の文字列

    """
    result = f'{status["horsename"]}の近況更新\n'
    result += status['status_date'].strftime('%y/%m/%d') + '\n'
    result += status['status']
    return result
