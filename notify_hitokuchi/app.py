"""一口出資馬の情報通知."""
import logging
from datetime import datetime, timedelta, timezone

import mojimoji
from aws_xray_sdk.core import patch_all

import carrot
import sqs
import settings
import yushun

patch_all()

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Lambda handler.

    Arguments:
        event {dict} -- Event data
        context {object} -- Lambda Context runtime methods and attributes

    """
    del context

    logger.info('start: event=%s', event)

    today = get_jstdate_from_isoformat(event['time'])

    yushun_statuses = yushun.get_horse_latest_statuses(today)
    carrot_statuses = carrot.get_horse_latest_statuses()
    statuses = yushun_statuses + carrot_statuses

    logger.info('statuses=%s', statuses)

    messages = [format_status(status)
                for status in statuses if status['status_date'] == today]

    logger.info('messages=%s', messages)

    if messages:
        sqs.send(settings.SQS_URL, settings.WEBHOOK_NAME, messages)

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
    result = f'{status["horse_name"]}の近況更新\n'
    result += status['status_date'].strftime('%y/%m/%d') + '\n'
    result += mojimoji.zen_to_han(status['status'], kana=False)
    return result
