"""S3からの値取得."""

import logging
import boto3
import json
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
client = boto3.client('s3')


def read_json(s3url: str):
    """S3からのJSONファイルを返す."""
    parse_result = urlparse(s3url)
    bucket = parse_result.netloc
    key = parse_result.path.lstrip('/')
    response = client.get_object(Bucket=bucket, Key=key)
    body = response['Body'].read()
    return json.loads(body)
