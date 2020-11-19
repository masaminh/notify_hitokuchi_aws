"""設定情報."""
import os
from os.path import dirname, join
from dotenv import load_dotenv
import boto3
from typing import Dict, List

load_dotenv(join(dirname(__file__), '.env'))
ssm = boto3.client('ssm')


def _get_environment(varname: str) -> str:
    var = os.environ.get(varname)
    return var if var is not None else ''


def _get_parameters(prefix: str, names: List[str]) -> Dict[str, str]:
    response = ssm.get_parameters(Names=[(prefix + x) for x in names])
    response_dict: Dict[str, str] = {
        x['Name']: x['Value'] for x in response['Parameters']}
    result = {n: response_dict[prefix + n]
              if (prefix + n) in response_dict else '' for n in names}
    return result


prefix: str = f'/{_get_environment("STAGE")}/NotifyHitokuchi/'
parameters = _get_parameters(prefix,
                             ['Carrot/UserId',
                              'Carrot/Password',
                              'Yushun/HorseId',
                              'WebhookName'])

CARROT_USERID = parameters['Carrot/UserId']
CARROT_PASSWORD = parameters['Carrot/Password']
YUSHUN_HORSE_ID = parameters['Yushun/HorseId']
SQS_URL = _get_environment('SQSURL')
WEBHOOK_NAME = parameters['WebhookName']
