"""carrotclub.netから情報取得する."""
import time
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests import Session

import settings


def get_horse_latest_statuses():
    """キャロットクラブ馬の直近の近況を返す.

    Returns:
        list -- 近況のリスト

    """
    session = Session()
    response = session.post(
        url='https://carrotclub.net/office/memlogin_redirect.asp',
        data={'ID': settings.CARROT_USERID, 'PW': settings.CARROT_PASSWORD, 'x': 5, 'y': 5})
    soup = BeautifulSoup(response.content, 'html5lib')
    a_elements = soup.find('section', id='panel-1').find_all('a')
    myhorse_links = (x.get('href') for x in a_elements)
    time.sleep(1)

    statuses = []

    for link in myhorse_links:
        url = urljoin(response.url, link)
        last_status = get_horse_latest_status(session, url)
        statuses.append(last_status)

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
    status['horse_name'] = soup.find('title').string.split()[0]
    state_ul = soup.find('ul', class_='KinkyoList')
    li_elements = state_ul.find_all('li')
    first_line = li_elements[0].text.split()
    status['status_date'] = datetime.strptime(first_line[0], '%y/%m/%d').date()
    status['status'] = str(li_elements[1].string)

    return status


def main():
    """メイン関数(試験用)."""
    from pprint import pprint

    last_statuses = get_horse_latest_statuses()
    pprint(last_statuses)


if __name__ == "__main__":
    main()
