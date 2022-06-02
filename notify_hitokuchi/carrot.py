"""carrotclub.netから情報取得する."""
import logging
import time
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests import Session

import settings

logger = logging.getLogger()


class ParseError(Exception):
    pass


def get_horse_latest_statuses():
    """キャロットクラブ馬の直近の近況を返す.

    Returns:
        list -- 近況のリスト

    """
    if not settings.CARROT_ENABLED:
        return []

    session = Session()
    response = session.post(
        url='https://carrotclub.net/office/memlogin_redirect.asp',
        data={
            'ID': settings.CARROT_USERID,
            'PW': settings.CARROT_PASSWORD,
            'x': 5,
            'y': 5})
    soup = BeautifulSoup(response.content, 'html5lib')
    a_elements = soup.find('section', id='panel-1').find_all('a')
    myhorse_links = (x.get('href') for x in a_elements)
    time.sleep(1)

    statuses = []

    for link in myhorse_links:
        url = urljoin(response.url, link)

        try:
            last_status = get_horse_latest_status(session, url)
        except ParseError as e:
            logger.warning(f'carrot: parse error: url={url}, message={e}')
        else:
            logger.info(
                'carrot: latest_status: url=%s, status_date=%s',
                url, last_status['status_date'])
            statuses.append(last_status)

        time.sleep(1)

    return statuses


def get_horse_latest_status(session, url):
    """指定馬の直近の近況情報を返す.

    Arguments:
        session {Session} -- 認証済みのセッション
        url {str} -- 馬を指定するurl

    Returns:
        dict -- 近況

    """
    status = dict()

    response = session.get(url)
    soup = BeautifulSoup(response.content, 'html5lib')
    horse_name_tag = soup.select_one('.umaHead h1')

    if horse_name_tag is None:
        raise ParseError('not found: ".umaHead h1"')

    status['horse_name'] = horse_name_tag.text
    li_element_tag = soup.select_one('ul.hose-lst1 > li:first-of-type')

    if li_element_tag is None:
        raise ParseError('not found: "ul.hose-lst1 > li:first-of-type"')

    first_line_tag = li_element_tag.select_one('h3')

    if first_line_tag is None:
        raise ParseError('not found: "h3"')

    first_line_string = first_line_tag.text.strip()
    status['status_date'] = datetime.strptime(
        first_line_string.split()[0], '%y/%m/%d').date()
    li_element_tag_strings = list(li_element_tag.strings)
    status['status'] = li_element_tag_strings[-1].strip()

    return status


def main():
    """メイン関数(試験用)."""
    from pprint import pprint

    last_statuses = get_horse_latest_statuses()
    pprint(last_statuses)


if __name__ == "__main__":
    main()
