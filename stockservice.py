from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from starlette.responses import JSONResponse

import pymysql, json, process_data


today = datetime.now().strftime("%Y-%m-%d") # 오늘
stdday = (datetime.now() - relativedelta(years=5)).strftime("%Y-%m-%d") # 5년전 오늘
b4year = (datetime.now() - relativedelta(years=1)).strftime("%Y-%m-%d") # 1년전 오늘

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

    conn.commit()

    return data

def match_krx():
    sql = "select code, name from stock_krx"
    curs.execute(sql)
    temp = curs.fetchall()

    data = process_data.codelist(temp)

    js = json.dumps(data, ensure_ascii=False)

    conn.commit()

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

    sql = "select code from corp_krx ORDER BY RAND() LIMIT 12"
    curs.execute(sql)
    datas = curs.fetchall()

    for data in datas:
        sql = "select code, name, close, changes_ratio from stock_marcap where code = %s and date = %s"
        curs.execute(sql, (data[0], last_day))
        temp = curs.fetchall()

        dic = process_data.matchrecom(temp)
        dict.update(dic)
    
    return dict

def stock_info(code):
    sql = "select sm.*, ck.sector from stock_marcap sm inner join corp_krx as ck \
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

    sql = "select per, pbr from stock_marcap where name = %s and date = %s"
    curs.execute(sql, (code, last_day))
    temp = curs.fetchall()
        
    if len(temp) == 0:
        dic = {"per": 0, "pbr": 0}
    else:
        dic = {"per": temp[0][0], "pbr":temp[0][1]}

    res.update(dic)
    conn.commit()

    return res

def sector_pebr(code):
    sql = "select sector from corp_krx where code = %s"
    curs.execute(sql, code)
    data = curs.fetchall()

    sector = data[0][0]

    sql = "select date, sector_per, sector_pbr, sector_psr from stock_sector where sector = %s and date between %s and %s"
    curs.execute(sql, (sector, b4year, today))
    datas = curs.fetchall()

    res = process_data.sector2dict(datas)
    return res

# 기업의 적정주가 목표 4가지
def get_evalutation(code):
    # 1. EPS * ROE (분기)
    sql = "select eps, roe from stock_indicator where code = %s ORDER BY date DESC limit 4"
    curs.execute(sql, code)
    datas = curs.fetchall()

    if len(datas) == 0:
        return "잘못된 기업명"

    conn.commit()
    eps = sum(data[0] for data in datas)
    roe = datas[0][1]

    if datas[-3][1] < datas[-2][1] < datas[-1][1]: # ROE 가 3년연속 상승 이라면?
        s_rim_roe = datas[-1][1]
    else:
        s_rim_roe = round((datas[-3][1] + (datas[-2][1] * 2) + (datas[-1][1] * 3)) / 6, 2)

    eval1 = eps * roe

    # 2. EPS * PBR/PER (일일)
    sql = "select per, pbr, stocks from stock_marcap where code = %s ORDER BY date DESC limit 1"
    curs.execute(sql, code)
    datas = curs.fetchall()
    conn.commit()

    s_roe = round((datas[0][1] / datas[0][0]) * 100, 2)
    
    eval2 = eps * s_roe

    # 3. S-Rim 적정주가
    sql = "select equity, equity_non from stock_statements where code = %s ORDER BY date DESC limit 1"
    curs.execute(sql, code)
    datas = curs.fetchall()
    conn.commit()

    equity = datas[0][0] - datas[0][1] # 자본총계 (지배)
    rate = 10.2 # 한국 신용평가의 BBB- 등급 채권의 5년 수익률 
    
    # 보통주 + 우선주
    sql = "select stocks from stock_marcap where code like %s and date = %s"
    curs.execute(sql, (code[:5]+"%", last_day))
    datas = curs.fetchall()

    if len(datas) == 0:
        # 값이 안 긁히면 거래정지 or 상장폐지
        print(code + " 이 기업은 거래정지 or 상장폐지된 기업")  
    else:
        # 보통주 + 모든 우선주 주식 수
        total_stock = sum(data[0] for data in datas)

    eval3 = round((equity * (s_rim_roe / rate)) / total_stock, 2)

    return process_data.evulation2json(eval1, eval2, eval3)


