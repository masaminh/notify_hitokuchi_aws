"""友駿ホームページから情報を取得する."""
import logging
import re
import time
from datetime import date, datetime
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup

import settings

logger = logging.getLogger()


def get_horse_latest_statuses(today):
    """友駿馬の直近の近況を返す.

    Arguments:
        today {date} -- 今日の日付

    Returns:
        list -- 近況のリスト

    """
    if not settings.YUSHUN_ENABLED:
        return []

    statuses = []

    for horseid in settings.YUSHUN_HORSE_ID.split(';'):
        status = get_horse_latest_status(today, horseid)
        logger.info(
            'yushun: latest_status: horseid=%s, status_date=%s',
            horseid, status['status_date'])
        statuses.append(status)
        time.sleep(1)

    return statuses


def get_horse_latest_status(today, horseid):
    """指定馬の直近の近況情報を返す.

    Arguments:
        today {date} -- 今日の日付
        horseid {str} -- 馬のID。horseno=487&bornid=1だったら487-1と指定する

    Returns:
        dict -- 近況

    """
    result = dict()

    horseno, bornid = horseid.split('-')
    qs = urlencode({'horseno': horseno, 'bornid': bornid})
    url = urljoin('http://www.yushun-members.com/news/kiji.cgi', '?' + qs)
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html5lib')
    result['horse_name'] = soup.select_one(
        'tbody tr:nth-child(2) td').string.split()[0]
    datestr = soup.select_one('tbody tr:nth-child(7) td').string
    result['status'] = soup.select_one(
        'tbody tr:nth-child(7) td:nth-child(2)').text

    m = re.fullmatch(r'(\d{1,2})月(\d{1,2})日', datestr)
    if m:
        month = int(m.group(1))
        day = int(m.group(2))
        year = today.year
        if month > today.month:
            year -= 1
        result['status_date'] = date(year, month, day)
    else:
        result['status_date'] = None

    return result


def main():
    """メイン関数(試験用)."""
    from argparse import ArgumentParser
    from pprint import pprint

    p = ArgumentParser()
    p.add_argument('--today', default=date.today().strftime('%Y-%m-%d'))
    p.add_argument('horseid', nargs='*')
    args = p.parse_args()
    today = datetime.strptime(args.today, '%Y-%m-%d').date()

    if args.horseid:
        for horseid in args.horseid:
            last_status = get_horse_latest_status(today, horseid)
            pprint(last_status)
    else:
        last_statuses = get_horse_latest_statuses(today)
        pprint(last_statuses)


if __name__ == '__main__':
    main()
