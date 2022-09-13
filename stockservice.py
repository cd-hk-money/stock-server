from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from starlette.responses import JSONResponse

import pymysql, json, process_data

today = datetime.now().strftime("%Y-%m-%d") # 오늘
stdday = (datetime.now() - relativedelta(years=5)).strftime("%Y-%m-%d") # 5년전 오늘
b4year = (datetime.now() - relativedelta(years=1)).strftime("%Y-%m-%d") # 1년전 오늘
b4_3year = (datetime.now() - relativedelta(years=3)).strftime("%Y-%m-%d") # 3년전 오늘
conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="1234", db="capstone", charset="utf8")
curs = conn.cursor()
conn.commit()

def lastday():
    sql = "select date from stock_marcap ORDER BY date DESC limit 1"
    curs.execute(sql)
    data = curs.fetchall()

    conn.commit()

    return data[0][0]

temp = lastday()
last_day = temp

def match_corp():
    sql = "select code, name from corp_krx"
    curs.execute(sql)
    temp = curs.fetchall()

    data = process_data.codelist(temp)

    js = json.dumps(data, ensure_ascii=False)

    return data

def match_krx():
    sql = "select code, name from stock_krx"
    curs.execute(sql)
    temp = curs.fetchall()

    data = process_data.codelist(temp)

    js = json.dumps(data, ensure_ascii=False)

    return data

def find_daily_total():
    sql = "Select * from daily_total where date between %s and %s"
    curs.execute(sql, (stdday, today))
    temp = list(curs.fetchall())

    data = process_data.dateisidx(temp)
    js = json.dumps(data, ensure_ascii=False)

    conn.commit()

    return data

def daily_rank():
    #시총 TOP10
    sql = "select * from stock_marcap where date = %s ORDER BY marcap DESC limit 50" 
    curs.execute(sql, last_day)
    data = curs.fetchall()

    dict1 = process_data.findtop("marcap", data)

    #떡상 TOP10
    sql = "select * from stock_marcap where date = %s ORDER BY changes_ratio DESC limit 50" 
    curs.execute(sql, last_day)
    data = curs.fetchall()

    dict2 = process_data.findtop("change_incr", data)

    #떡락 TOP 10
    sql = "select * from stock_marcap where date = %s ORDER BY changes_ratio ASC limit 50" 
    curs.execute(sql, last_day)
    data = curs.fetchall()

    dict3 = process_data.findtop("change_redu", data)

    #거래량 TOP 10
    sql = "select * from stock_marcap where date = %s ORDER BY volume DESC limit 50" 
    curs.execute(sql, last_day)
    data = curs.fetchall()

    dict4 = process_data.findtop("volume", data)
    
    res = dict(dict1, **dict2, **dict3, **dict4)

    conn.commit()

    return res

def find_recommand():
    dict = defaultdict(list)

    sql = "select code from daily_evalutation where date = %s and evalutation_score between -50 and -30 order by rand() LIMIT 12"
    curs.execute(sql, last_day)
    datas = curs.fetchall()

    for data in datas:
        sql = "select code, name, close, changes_ratio from stock_marcap where code = %s and date = %s"
        curs.execute(sql, (data[0], last_day))
        temp = curs.fetchall()

        dic = process_data.matchrecom(temp)
        dict.update(dic)
    
    return dict

def stock_info(code):
    sql = "select sm.*, ck.sector from stock_marcap sm inner join stock_krx as ck \
        on sm.code = ck.code \
        where sm.code = %s ORDER BY date DESC limit 1"
        
    curs.execute(sql, code)
    data = curs.fetchall()

    if len(data) == 0:
        conn.commit()

        return "잘못된 기업명입니다~"

    data = data[0]
    conn.commit()

    return data

def graph2weeks(code):
    sql = "select date, close from stock_marcap where code = %s and date >= DATE_ADD(%s, INTERVAL -14 DAY) ORDER BY date ASC limit 14"
    curs.execute(sql, (code, last_day))
    data = curs.fetchall()
    
    if len(data) == 0:
        
        conn.commit()

        return "잘못된 기업명입니다~"
    
    conn.commit()
    
    res = {}
    res1 = process_data.data2graph(data)
    res2 = process_data.data2graph2(data)
    
    res.update(res1)
    res.update(res2)
    
    return res

def graph5year(code):
    sql = "select date, close from stock_marcap where code = %s and date >= DATE_ADD(%s, INTERVAL -5 YEAR)"
    curs.execute(sql, (code, last_day))
    data = curs.fetchall()
    
    if len(data) == 0:
        conn.commit()
    
        return "잘못된 기업명입니다~"

    conn.commit()
    
    res = {}
    res1 = process_data.data2graph(data)
    res2 = process_data.data2graph2(data)
    
    res.update(res1)
    res.update(res2)
    
    return res

def graphvolume5year(code):
    sql = "select date, volume from stock_marcap where code = %s and date >= DATE_ADD(%s, INTERVAL -5 YEAR)"
    curs.execute(sql, (code, last_day))
    data = curs.fetchall()
    
    if len(data) == 0:
        conn.commit()
    
        return "잘못된 기업명입니다~"

    conn.commit()
    
    res = {}
    res1 = process_data.data2graph(data)
    res2 = process_data.data2graph2(data)
    
    res.update(res1)
    res.update(res2)
    
    return res

def graph_detail(code, start, end):
    sql = "select date, close from stock_marcap where code = %s and date between %s and %s"
    curs.execute(sql, (code, start, end))
    data = curs.fetchall()
    if len(data) == 0:

        conn.commit()
    
        return "잘못된 기업명 or 해당 날짜 데이터가 없어요~"

    conn.commit()
    
    res = {}
    res1 = process_data.data2graph(data)    
    res2 = process_data.data2graph2(data)

    res.update(res1)
    res.update(res2)
    return res

def type2graph(type, code):
    if type == "ebitda":
        sql = "select date, ebitda from stock_statements where code = %s"
    elif type == "asset":
        sql = "select date, asset from stock_statements where code = %s"
    elif type == "equity":
        sql = "select date, equity from stock_statements where code = %s" 
    elif type == "liability":
        sql = "select date, liability from stock_statements where code = %s"
    elif type == "current_asset":
        sql = "select date, current_asset from stock_statements where code = %s"
    elif type == "profit":
        sql = "select date, profit from stock_statements where code = %s"
    elif type == "revenue":
        sql = "select date, revenue from stock_statements where code = %s"
    elif type == "cash":
        sql = "select date, cash from stock_statements where code = %s"
    elif type == "gross_margin":
        sql = sql = "select date, gross_margin from stock_statements where code = %s" 

    print(sql)
    curs.execute(sql, code)
    data = curs.fetchall()

    if len(data) == 0:
        conn.commit()
    
        return "재무제표가 없어요~"
    
    conn.commit()
    
    res = {}
    res1 = process_data.data2graph(data)
    res2 = process_data.data2graph3(data, type)
    
    res.update(res1)
    res.update(res2)
    
    return res

def find_statement(code):
    sql = "select * from stock_statements where code = %s ORDER BY date DESC limit 4"
    curs.execute(sql, code)
    
    data = curs.fetchall()
    res = process_data.state2dict(data)
    
    conn.commit()
    
    return res
   
def find_indicator(code):
    sql = "select * from stock_indicator where code = %s ORDER BY date DESC limit 4"
    curs.execute(sql, code)
    data = curs.fetchall()
    res = process_data.indi2dict(data)

    conn.commit()

    return res

# 기업이 해당하는 업종 평균 PER, PBR, PSR
def sector_pebr(code):
    sql = "select sector from corp_krx where code = %s"
    curs.execute(sql, code)
    data = curs.fetchall()

    sector = data[0][0]

    sql = "select date, sector_per, sector_pbr, sector_psr from stock_sector_daily where sector = %s and date between %s and %s"
    curs.execute(sql, (sector, b4year, today))
    datas = curs.fetchall()

    res = process_data.sector2dict(datas)
    return res

def sector_ebps(code):
    sql = "select sector from corp_krx where code = %s"
    curs.execute(sql, code)
    data = curs.fetchall()

    sector = data[0][0]

    sql = "select date, sector_eps, sector_bps, sector_roe from stock_sector where sector = %s ORDER by date DESC limit 4"
    curs.execute(sql, sector)
    datas = curs.fetchall()

    res = process_data.sectorqu2dict(datas)
    return res

# 기업의 적정주가 목표 4가지
def get_evalutation(code):
    sql = "select date, proper_price, s_rim from stock_indicator where code = %s order by date DESC limit 12"
    curs.execute(sql, code)
    data = list(curs.fetchall())

    data.sort(key = lambda x : x[0])

    return process_data.evulation2json(data)

def get_daily_evalutation(code):
    # 갖고와서 뿌려주기
    sql = "select date, daily_proper_price from daily_evalutation where code = %s and date >= %s"
    curs.execute(sql, (code, b4_3year))
    data = list(curs.fetchall())

    return process_data.daily_evalu(data)

def findDailyIndicator(code):
    sql = "select date, per, pbr, psr from stock_marcap where code = %s and date >= %s"
    curs.execute(sql, (code, b4year))
    data = list(curs.fetchall())

    return process_data.daily_indicator(data)