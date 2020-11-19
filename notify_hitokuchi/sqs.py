"""SQSへのメッセージ投入関数."""

import logging
import boto3
import json
from typing import List

logger = logging.getLogger(__name__)
client = boto3.client('sqs')


def send(url: str, webhookname: str, messages: List[str]) -> None:
    """SQS経由でWebhookにメッセージを送る.

    Args:
        url (str): SQSのURL
        webhookname (str): Webhook名
        messages (List[str]): メッセージのリスト
    """
    logger.info(f'sqs.send: sending {len(messages)} message(s).')
    splited = (messages[idx:idx + 10] for idx in range(0, len(messages), 10))

    for msgs in splited:
        msg_dicts = ({'webhookname': webhookname,
                      'message': msg} for msg in msgs)
        entries = [{'Id': str(i), 'MessageBody': json.dumps(d)}
                   for i, d in enumerate(msg_dicts)]
        client.send_message_batch(QueueUrl=url, Entries=entries)
        logger.info(
            f'sqs.send: send_message_batch sent {len(entries)} message(s).')

    logger.info(f'sqs.send: sent {len(messages)} message(s).')
