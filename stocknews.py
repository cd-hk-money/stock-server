import urllib
import requests
import re
from bs4 import BeautifulSoup

def crawl_news(name):
    #1. 네이버 증권에 Request 요청
    url = "https://finance.naver.com/news/news_search.naver?q={q}&x=21&y=5"
    q = name
    q_enc = urllib.parse.quote_plus(q, encoding='euc-kr')

    res = requests.get(url.format(q = q_enc))

    #2. 필요한 데이터 파싱하기
    #BS 객체 생성, 뉴스 첫 페이지 긁어오기
    soup = BeautifulSoup(res.text, 'lxml')
    elem_news = soup.select_one('div.newsSchResult  .newsList')

    #증권 첫 페이지의 모든 뉴스 제목 + 링크
    elems_subject = elem_news.select('.articleSubject')

    #본문 내용 미리보기
    elems_summary = elem_news.select('.articleSummary')


    #3. 사용하기 편하게 가공하기
    #제목만 뽑아 오고 싶다면
    title = elems_subject[0].text.strip()

    #기사 링크만 뽑아 오고 싶다면
    link = elems_subject[0].a.get('href')
    parse_res = urllib.parse.urlparse(url)
    item_url_pre = '{}://{}'.format(parse_res.scheme, parse_res.netloc)

    #기사 본문 미리보기만 뽑아 오고 싶다면
    content = re.sub('\n|\t', '', elems_summary[0].text.strip())

    #4. 한번에 종합하기
    res = []
    for sub, sum in zip(elems_subject, elems_summary):
        item_url = '{}{}'.format(item_url_pre, sub.a.get('href'))
        item = {
            'subject': sub.text.strip(),
            'summary': re.sub('\n|\t', '', sum.text.strip()),
            'url': item_url, 
        }
        res.append(item)
    
    return res