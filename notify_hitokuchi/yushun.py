"""友駿ホームページから情報を取得する."""
import logging
import re
import time
from datetime import date, datetime
from urllib.parse import urlencode, urljoin
from typing import TypeVar, Optional, Dict, List

import requests
from bs4 import BeautifulSoup

import settings
import s3

logger = logging.getLogger()

KINKYO_URL = 'https://ssl.yushun-members.com/news3/kinkyo.cgi'
BORN_IDS = (1, 2, 3)  # 1: 関東馬, 2: 関西馬, 3: 地方馬


def get_horse_latest_statuses(today):
    """友駿馬の直近の近況を返す.

    horses.json のうち yushun キーを持つ馬を対象に、近況一覧ページで馬名を照合して
    詳細ページを取得する.

    Arguments:
        today {date} -- 今日の日付

    Returns:
        list -- 近況のリスト

    """
    if not settings.YUSHUN_ENABLED:
        return []

    horses = s3.read_json(settings.HORSES_JSON_URI)

    if horses is None or "horses" not in horses:
        return []

    names = [horse["horseName"] for horse in horses["horses"]
             if "yushun" in horse and horse.get("horseName")]

    if not names:
        return []

    entries = get_kinkyo_entries()
    return get_statuses_by_names(today, names, entries, skip_not_updated=True)


def get_statuses_by_names(today, names: List[str], entries: Dict[str, Dict],
                          skip_not_updated: bool) -> List[Dict]:
    """馬名リストに対応する近況を返す.

    Arguments:
        today {date} -- 今日の日付
        names {List[str]} -- 馬名のリスト
        entries {Dict[str, Dict]} -- get_kinkyo_entries() の結果
        skip_not_updated {bool} -- 一覧の更新日が今日でない馬は詳細を取得しない

    Returns:
        list -- 近況のリスト

    """
    statuses = []

    for name in names:
        entry = entries.get(normalize_name(name))

        if entry is None:
            logger.warning('yushun: not found in kinkyo list: %s', name)
            continue

        updated = entry['updated']
        if skip_not_updated and updated is not None and updated != today:
            logger.info('yushun: not updated today: %s (updated=%s)',
                        name, updated)
            continue

        status = get_horse_latest_status(today, entry['url'])
        time.sleep(1)

        if status is None:
            continue

        statuses.append(status)

    return statuses


def get_kinkyo_entries() -> Dict[str, Dict]:
    """近況一覧ページ(関東・関西・地方)から馬名ごとの詳細URLと更新日を返す.

    Returns:
        Dict[str, Dict] -- {正規化した馬名: {'url': 詳細URL, 'updated': 更新日}}

    """
    entries: Dict[str, Dict] = {}

    for i, bornid in enumerate(BORN_IDS):
        if i > 0:
            time.sleep(1)

        url = urljoin(KINKYO_URL, '?' + urlencode({'bornid': bornid}))

        try:
            logger.info('requesting: %s', url)
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            entries.update(parse_kinkyo_page(r.content, r.url))
        except Exception as e:
            logger.warning('yushun: get_kinkyo_entries: url=%s: %s', url, e)

    logger.info('yushun: kinkyo entries: %d', len(entries))
    return entries


def parse_kinkyo_page(content: bytes, base_url: str) -> Dict[str, Dict]:
    """近況一覧ページをパースする.

    Arguments:
        content {bytes} -- ページのHTML
        base_url {str} -- 相対リンク解決用のURL

    Returns:
        Dict[str, Dict] -- {正規化した馬名: {'url': 詳細URL, 'updated': 更新日}}

    """
    entries: Dict[str, Dict] = {}
    soup = BeautifulSoup(content, 'html5lib')

    for a in soup.select('tr a[href^="kiji.cgi"]'):
        name = normalize_name(a.get_text())
        if not name:
            continue

        tr = a.find_parent('tr')
        tds = tr.find_all('td', recursive=False) if tr else []
        updated = None
        if tds:
            try:
                updated = date.fromisoformat(tds[-1].get_text().strip())
            except ValueError:
                updated = None

        entries[name] = {
            'url': urljoin(base_url, a['href']),
            'updated': updated,
        }

    return entries


def normalize_name(name: str) -> str:
    """馬名を照合用に正規化する(全角含む空白を除去).

    Arguments:
        name {str} -- 馬名

    Returns:
        str -- 正規化した馬名

    """
    return ''.join(name.split())


def get_horse_latest_status(today, url) -> Optional[Dict]:
    """指定馬の直近の近況情報を返す.

    Arguments:
        today {date} -- 今日の日付
        url {str} -- 馬の近況詳細ページ(kiji.cgi)のURL

    Returns:
        dict -- 近況

    """
    result = dict()

    try:
        logger.info('requesting: %s', url)
        r = requests.get(url, timeout=30)
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
        logger.warning('yushun: get_horse_latest_status: url=%s: %s', url, e)
        return None

    logger.info(
        'yushun: get_horse_latest_status: url=%s, result=%s',
        url,
        result)
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
    p.add_argument('horse_name', nargs='*')
    args = p.parse_args()
    today = datetime.strptime(args.today, '%Y-%m-%d').date()

    if args.horse_name:
        entries = get_kinkyo_entries()
        pprint(get_statuses_by_names(
            today, args.horse_name, entries, skip_not_updated=False))
    else:
        last_statuses = get_horse_latest_statuses(today)
        pprint(last_statuses)


if __name__ == '__main__':
    main()
