# uvicorn testserver:app --reload

from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from starlette.responses import JSONResponse

import pymysql, json, process_data

today = datetime.now().strftime("%Y-%m-%d")
stdday = (datetime.now() - relativedelta(years=5)).strftime("%Y-%m-%d")

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
    sql = "select code, name, close, marcap from stock_marcap where date = %s ORDER BY marcap DESC limit 50" 
    curs.execute(sql, last_day)
    data = curs.fetchall()

    dict1 = process_data.findtop("marcap", data)

    #떡상 TOP10
    sql = "select code, name, close, changes_ratio from stock_marcap where date = %s ORDER BY changes_ratio DESC limit 50" 
    curs.execute(sql, last_day)
    data = curs.fetchall()

    dict2 = process_data.findtop("change_incr", data)

    #떡락 TOP 10
    sql = "select code, name, close, changes_ratio from stock_marcap where date = %s ORDER BY changes_ratio ASC limit 50" 
    curs.execute(sql, last_day)
    data = curs.fetchall()

    dict3 = process_data.findtop("change_redu", data)

    #거래량 TOP 10
    sql = "select code, name, close, volume from stock_marcap where date = %s ORDER BY volume DESC limit 50" 
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

def stock_info(name):
    sql = "select * from stock_marcap where name = %s ORDER BY date DESC limit 1"
    curs.execute(sql, name)
    data = curs.fetchall()
    
    if len(data) == 0:
        conn.commit()

        return "잘못된 기업명입니다~"

    data = data[0]
    
    conn.commit()

    return data

def graph2weeks(name):
    sql = "select date, close from stock_marcap where name = %s and date >= DATE_ADD(%s, INTERVAL -14 DAY) ORDER BY date ASC limit 14"
    curs.execute(sql, (name, last_day))
    data = curs.fetchall()
    
    if len(data) == 0:
        
        conn.commit()

        return "잘못된 기업명입니다~"
    
    res = process_data.data2grahp(data)

    conn.commit()

    return res

def graph5year(name):
    sql = "select date, close from stock_marcap where name = %s and date >= DATE_ADD(%s, INTERVAL -5 YEAR)"
    curs.execute(sql, (name, last_day))
    data = curs.fetchall()
    
    if len(data) == 0:
        conn.commit()
    
        return "잘못된 기업명입니다~"

    res = process_data.data2grahp(data)

    conn.commit()

    return res

def graph_detail(name, start, end):
    sql = "select date, close from stock_marcap where name = %s and date between %s and %s"
    curs.execute(sql, (name, start, end))
    data = curs.fetchall()
    if len(data) == 0:

        conn.commit()
    
        return "잘못된 기업명 or 해당 날짜 데이터가 없어요~"

    res = process_data.data2grahp(data)

    conn.commit()

    return res

def type2graph(type, name):
    sql = "select code from corp_krx where name = %s"
    curs.execute(sql, name)
    temp = curs.fetchall()
    
    if len(temp) == 0:
        conn.commit()
    
        return "선물 혹은 잘못된 기업명이에요~"

    code = temp[0][0]
    
    if type == "ebitda":
        sql = "select date, ebitda from stock_statements where code = %s"
    elif type == "revenue":
        sql = "select date, revenue from stock_statements where code = %s"

    curs.execute(sql, code)
    data = curs.fetchall()

    if len(data) == 0:
        conn.commit()
    
        return "재무제표가 없어요~"
    
    res = process_data.data2grahp(data)

    conn.commit()

    return res

def find_statement(name):
    sql = "select code from corp_krx where name = %s"
    curs.execute(sql, name)
    temp = curs.fetchall()
    
    if len(temp) == 0:
        conn.commit()
    
        return "선물 혹은 잘못된 기업명이에요~"

    code = temp[0][0]

    sql = "select * from stock_statements where code = %s ORDER BY date DESC limit 4"
    curs.execute(sql, code)
    
    data = curs.fetchall()
    res = process_data.state2dict(data)
    
    conn.commit()
    
    return res
   
def find_indicator(name):
    sql = "select code from corp_krx where name = %s"
    curs.execute(sql, name)
    temp = curs.fetchall()
        
    if len(temp) == 0:    
       return "선물 혹은 잘못된 기업명이에요~"
    conn.commit()
    code = temp[0][0]

    sql = "select * from stock_indicator where code = %s ORDER BY date DESC limit 4"
    curs.execute(sql, code)
    data = curs.fetchall()
    res = process_data.indi2dict(data)
        
    conn.commit()

    sql = "select per, pbr from stock_marcap where name = %s and date = %s"
    curs.execute(sql, (name, last_day))
    temp = curs.fetchall()
        
    if len(temp) == 0:
        dic = {"per": 0, "pbr": 0}
    else:
        dic = {"per": temp[0][0], "pbr":temp[0][1]}

    res.update(dic)

    conn.commit()

    return res