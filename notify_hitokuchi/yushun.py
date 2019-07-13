"""友駿ホームページから情報を取得する."""
import re
from datetime import date, datetime
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup


def get_horse_latest_status(today, horseid):
    """指定馬の直近の近況情報を返す.

    Arguments:
        horseid {str} -- 馬のID。horseno=487&bornid=1だったら487-1と指定する

    """
    result = dict()

    horseno, bornid = horseid.split('-')
    qs = urlencode({'horseno': horseno, 'bornid': bornid})
    url = urljoin('http://www.yushun-members.com/news/kiji.cgi', '?' + qs)
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'lxml')
    result['horsename'] = soup.select_one('tbody tr:nth-child(2) td').string.split()[0]
    datestr = soup.select_one('tbody tr:nth-child(7) td').string
    result['status'] = soup.select_one('tbody tr:nth-child(7) td:nth-child(2)').text

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
    p.add_argument('horseid', nargs='+')
    args = p.parse_args()
    today = datetime.strptime(args.today, '%Y-%m-%d').date()


    for horseid in args.horseid:
        last_status = get_horse_latest_status(today, horseid)
        pprint(last_status)

if __name__ == '__main__':
    main()
