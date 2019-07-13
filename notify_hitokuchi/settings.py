"""設定情報."""
import os
from os.path import dirname, join

from dotenv import load_dotenv

load_dotenv(join(dirname(__file__), '.env'))

YUSHUN_HORSE_ID = os.environ.get('YUSHUN_HORSE_ID')
LINE_NOTIFY_ACCESS_TOKEN = os.environ.get('LINE_NOTIFY_ACCESS_TOKEN')
