"""友駿ホームページから情報を取得する."""
import logging
import re
import time
from datetime import date, datetime
from urllib.parse import urlencode, urljoin
from typing import TypeVar, Optional, Dict

import requests
from bs4 import BeautifulSoup

import settings
import s3

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

    horses = s3.read_json(settings.HORSES_JSON_URI)

    if horses is None or "horses" not in horses:
        return []

    yushun_infos = [horse["yushun"]
                    for horse in horses["horses"] if "yushun" in horse]
    horse_ids = [yushun_info["horseId"]
                 for yushun_info in yushun_infos if "horseId" in yushun_info]

    for horseid in horse_ids:
        status = get_horse_latest_status(today, horseid)

        if status is None:
            continue

        logger.info(
            'yushun: latest_status: horseid=%s, status_date=%s',
            horseid, status['status_date'])
        statuses.append(status)
        time.sleep(1)

    return statuses


def get_horse_latest_status(today, horseid) -> Optional[Dict]:
    """指定馬の直近の近況情報を返す.

    Arguments:
        today {date} -- 今日の日付
        horseid {str} -- 馬のID。horseno=487&bornid=1だったら487-1と指定する

    Returns:
        dict -- 近況

    """
    result = dict()

    try:
        horseno, bornid = horseid.split('-')
        qs = urlencode({'horseno': horseno, 'bornid': bornid})
        url = urljoin('http://www.yushun-members.com/news/kiji.cgi', '?' + qs)
        logger.info('requesting: %s', url)
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html5lib')
        horse_name_tag = not_none(soup.select_one('tbody tr:nth-child(2) td'))
        result['horse_name'] = not_none(horse_name_tag.string).split()[0]
        date_str_tag = not_none(soup.select_one('tbody tr:nth-child(7) td'))
        datestr = not_none(date_str_tag.string)
        status_tag = not_none(soup.select_one(
            'tbody tr:nth-child(7) td:nth-child(2)'))
        result['status'] = status_tag.text

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
    except Exception as e:
        logger.warning('yushun: get_horse_latest_status: %s', e)
        return None

    return result


T = TypeVar('T')


def not_none(value: Optional[T]) -> T:
    """引数がNone以外であることを保証する. Noneだったら例外発生させる.

    Args:
        value (Optional[T]): 保証させたい値

    Raises:
        ValueError: 引数値がNoneだった

    Returns:
        T: Noneでない値
    """
    if value is None:
        raise ValueError('value is None')
    return value


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
