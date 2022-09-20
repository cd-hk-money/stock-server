from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from numpy import double
import pymysql
import FinanceDataReader as fdr
from marcap import marcap_data
import csv
import schedule
import os
import state_cal

# KRXstock_List() : KOSPI 상장(상품 포함) & 순수 기업 리스트 DB
# marcap_List() : 1995 ~ 현재 모든 marcap 약 1200만개
# every_marcap() : 오늘 기준 marcap, 매일 pull & push
# stock_statement() : 재무제표 DB

# DB 연결
conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="1234", db="capstone", charset="utf8")
curs = conn.cursor()
conn.commit()

# 매일 할 일 (아침 7시 세팅)
#-----------------------------------------------------------------------------------#
today = datetime.now()
std_day = today - relativedelta(years=5)  
last_day = (datetime.strptime(state_cal.std_day(), "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

def every_do():
    os.system('cd marcap && git pull origin master')
    df = marcap_data(last_day, today)
    
    if len(df.index) == 0:
        print("today data none")
        pass
    else:
        df.to_csv("marcap_" + today.strftime("%Y-%m-%d") + ".csv", mode="w")
        print("today data ready & update start ...")
        every_marcap()
        # state_cal.union_table()

    
# schedule.every().day.at("07:00").do(every_do)
#-----------------------------------------------------------------------------------#

# 재무제표
def stock_statement():
    f = open("21_22_statement.csv", 'r', encoding="cp949")
    csvReader = csv.reader(f)

    for row in csvReader:
        if row[0] == "열1": #첫 행은 컬럼명이니까 PASS
            continue

        code = row[1].zfill(6)
        report_type = row[3]
        asset = double(row[4].replace(",", ""))
        equity = double(row[5].replace(",", ""))
        equity_non = double(row[6].replace(",", ""))
        liability = double(row[7].replace(",", ""))
        current_asset = double(row[8].replace(",", ""))
        profit = double(row[9].replace(",", ""))
        profit_non = double(row[10].replace(",", ""))
        revenue = double(row[11].replace(",", ""))
        cash = double(row[12].replace(",", ""))
        depriciation = double(row[13].replace(",", ""))
        ebitda = double(row[14].replace(",", ""))
        gross_margin = double(row[15].replace(",", ""))
        
        if report_type == "1분기보고서":
            date = row[2] + "-03"
        elif report_type == "반기보고서":
            date = row[2] + "-06"
        elif report_type == "3분기보고서":
            date = row[2] + "-09"
        elif report_type == "사업보고서":
            date = row[2] + "-12" 

        sql = "INSERT IGNORE INTO stock_statements_origin (code, date, type, asset, equity, equity_non, liability,\
             current_asset, profit, profit_non, revenue, cash, depriciation, ebitda, gross_margin) \
             values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        curs.execute(sql, (code, date, report_type, asset, equity, equity_non, liability, current_asset, profit, profit_non, revenue, cash, depriciation, ebitda, gross_margin))

        print(code + " " + report_type + " OK")

    conn.commit()
    f.close()
    conn.close()

# KRX to DB V1 
def KRXstock_List():
    stock = fdr.StockListing("KRX")
    stock.to_csv("KRXList.csv")

    f = open("KRXList.csv", 'r', encoding="UTF-8")
    csvReader = csv.reader(f)

    for row in csvReader:
        Code = row[1]
        Market = row[2]
        Name = row[3]
        Sector = row[4]
        Industry = row[5]
        
        if Code == "Symbol":
            continue        
        
        # KRX 전체
        sql = "INSERT IGNORE INTO stock_krx (code, market, name, sector, industry) values(%s, %s, %s, %s, %s)"
        curs.execute(sql, (Code, Market, Name, Sector, Industry))
        
        # 순수 상장 기업
        if Sector != "":
            sql = "INSERT IGNORE INTO corp_krx (code, market, name, sector, industry) values(%s, %s, %s, %s, %s)"
            curs.execute(sql, (Code, Market, Name, Sector, Industry))
    
    conn.commit()
    f.close()
    conn.close()

# Marcap Data to DB
# 1995 ~ 현재 까지 row 약 1200만개
def marcap_list():

    # csv 파일 만들기 위한 로직
    # df_old = marcap_data("1995-01-01", today)
    # df_old.to_csv("marcap_old.csv", mode="w")
    f = open("marcap_old.csv", 'r', encoding="UTF-8")
    csvReader = csv.reader(f)
    
    for row in csvReader:
        date = row[0]
        code = row[1]
        name = row[2]
        market = row[3]
        close = row[5]
        changes = row[7]
        changesRatio = row[8]
        Open = row[9]
        high = row[10]
        low = row[11]
        volume = row[12]
        amount = row[13]
        marcap = row[14]
        stocks = row[15]
        
        if code == "Code":
            continue
        
        sql = "INSERT IGNORE INTO stock_marcap_origin (date, code, name, market, close, changes, changes_ratio, \
            open, high, low, volume, amount, marcap, stocks) \
                values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                
        curs.execute(sql, (date, code, name, market, close, changes, changesRatio, Open, high, low, \
            volume, amount, marcap, stocks))
        
        print(date, "query ok")
        
    conn.commit()
    f.close()
    conn.close()    

# 일일 주가 데이터 DB push
def every_marcap(): 
    f = open("marcap_" + today.strftime('%Y-%m-%d') + ".csv", 'r', encoding="UTF-8")
    csvReader = csv.reader(f)
    
    for row in csvReader:
        date = row[0]
        code = row[1]
        name = row[2]
        market = row[3]
        close = row[5]
        changes = row[7]
        changesRatio = row[8]
        Open = row[9]
        high = row[10]
        low = row[11]
        volume = row[12]
        amount = row[13]
        marcap = row[14]
        stocks = row[15]
        
        if code == "Code":
            continue
        
        sql = "INSERT IGNORE INTO stock_marcap_old (date, code, name, market, close, changes, changes_ratio, \
            open, high, low, volume, amount, marcap, stocks) \
                values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                
        curs.execute(sql, (date, code, name, market, close, changes, changesRatio, Open, high, low, \
            volume, amount, marcap, stocks))
        
        print(date, "query ok")
        
    conn.commit()
    f.close()
    conn.close()

#KOSPI, S&P500(NYSE), NASDAQ, US채권(1, 5, 10) -> DB
def daily_total():
    last_total = datetime.strptime(state_cal.total_day(), "%Y-%m-%d").date() + timedelta(days=1)

    df = fdr.DataReader('KS11', last_total)
    df.reset_index(drop = False, inplace = True)
    df = df.values.tolist()

    t = 'KOSPI'
    for row in df:
        date = row[0].strftime('%Y-%m-%d')
        close = row[1]
        op = row[2]
        high = row[3]
        low = row[4]
        volume = row[5]
        changes = row[6]

        sql = "INSERT INTO daily_total (date, type, close, open, high, low, volume, changes) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        curs.execute(sql, (date, t, close, op, high, low, volume, changes))

        print(date + " KOSPI OK")
    
    t = 'S&P500'
    df = fdr.DataReader('US500', last_total)
    df.reset_index(drop = False, inplace = True)
    df = df.values.tolist()

    for row in df:
        date = row[0].strftime('%Y-%m-%d')
        close = row[1]
        op = row[2]
        high = row[3]
        low = row[4]
        volume = row[5]
        changes = row[6]

        sql = "INSERT INTO daily_total (date, type, close, open, high, low, volume, changes) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        curs.execute(sql, (date, t, close, op, high, low, volume, changes))
        print(date + " S&P500 OK")

    t = "NASDAQ"
    df = fdr.DataReader('IXIC', last_total)
    df.reset_index(drop = False, inplace = True)
    df = df.values.tolist()

    for row in df:
        date = row[0].strftime('%Y-%m-%d')
        close = row[1]
        op = row[2]
        high = row[3]
        low = row[4]
        volume = row[5]
        changes = row[6]

        sql = "INSERT INTO daily_total (date, type, close, open, high, low, volume, changes) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        curs.execute(sql, (date, t, close, op, high, low, volume, changes))
        print(date + " NASDAQ OK")

    t = "US1YT"
    df = fdr.DataReader("US1YT=X", last_total)
    df.reset_index(drop = False, inplace=True)
    df = df.values.tolist()

    for row in df:
        date = row[0].strftime("%Y-%m-%d")
        close = row[1]
        op = row[2]
        high = row[3]
        low = row[4]
        changes = row[5]
        
        volume = 0 #채권은 거래량이 없다
        
        sql = "INSERT INTO daily_total (date, type, close, open, high, low, volume, changes) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        curs.execute(sql, (date, t, close, op, high, low, volume, changes))
        print(date + " US1YT OK")
        
    t = "US5YT"
    df = fdr.DataReader("US5YT=X", last_total)
    df.reset_index(drop = False, inplace=True)
    df = df.values.tolist()
    
    for row in df:
        date = row[0].strftime("%Y-%m-%d")
        close = row[1]
        op = row[2]
        high = row[3]
        low = row[4]
        changes = row[5]
        
        volume = 0 #채권은 거래량이 없다
        
        sql = "INSERT INTO daily_total (date, type, close, open, high, low, volume, changes) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        curs.execute(sql, (date, t, close, op, high, low, volume, changes))
        print(date + " US5YT OK")
        
    t = "US10YT"
    df = fdr.DataReader("US10YT=X", last_total)
    df.reset_index(drop = False, inplace=True)
    df = df.values.tolist()
    
    for row in df:
        date = row[0].strftime("%Y-%m-%d")
        close = row[1]
        op = row[2]
        high = row[3]
        low = row[4]
        changes = row[5]
        
        volume = 0 #채권은 거래량이 없다
        
        sql = "INSERT INTO daily_total (date, type, close, open, high, low, volume, changes) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        curs.execute(sql, (date, t, close, op, high, low, volume, changes))
        print(date + " US10YT OK")
    
    t = "USD/KRW"
    df = fdr.DataReader("USD/KRW", last_total)
    df.reset_index(drop = False, inplace=True)
    df = df.values.tolist()
    
    for row in df:
        date = row[0].strftime("%Y-%m-%d")
        close = row[1]
        op = row[2]
        high = row[3]
        low = row[4]
        changes = row[5]
        
        volume = 0 #환율은 거래량이 없다
        
        sql = "INSERT INTO daily_total (date, type, close, open, high, low, volume, changes) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        curs.execute(sql, (date, t, close, op, high, low, volume, changes))
        print(date + " USD/KRW OK")
    
    conn.commit()
    conn.close()

# 미국 국채 초기 세팅용 (2017-01-01 ~ 현재)
def us_bond():
    t = "US1YT"
    df = fdr.DataReader("US1YT=X", "2017-01-01")
    df.reset_index(drop = False, inplace=True)
    df = df.values.tolist()

    for row in df:
        date = row[0].strftime("%Y-%m-%d")
        close = row[1]
        op = row[2]
        high = row[3]
        low = row[4]
        changes = row[5]
        
        volume = 0 #채권은 거래량이 없다
        
        sql = "INSERT INTO daily_total (date, type, close, open, high, low, volume, changes) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        curs.execute(sql, (date, t, close, op, high, low, volume, changes))
        print(date + " US1YT OK")
        
    t = "US5YT"
    df = fdr.DataReader("US5YT=X", "2017-01-01")
    df.reset_index(drop = False, inplace=True)
    df = df.values.tolist()
    
    for row in df:
        date = row[0].strftime("%Y-%m-%d")
        close = row[1]
        op = row[2]
        high = row[3]
        low = row[4]
        changes = row[5]
        
        volume = 0 #채권은 거래량이 없다
        
        sql = "INSERT INTO daily_total (date, type, close, open, high, low, volume, changes) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        curs.execute(sql, (date, t, close, op, high, low, volume, changes))
        print(date + " US5YT OK")
        
    t = "US10YT"
    df = fdr.DataReader("US10YT=X", "2017-01-01")
    df.reset_index(drop = False, inplace=True)
    df = df.values.tolist()
    
    for row in df:
        date = row[0].strftime("%Y-%m-%d")
        close = row[1]
        op = row[2]
        high = row[3]
        low = row[4]
        changes = row[5]
        
        volume = 0 #채권은 거래량이 없다
        
        sql = "INSERT INTO daily_total (date, type, close, open, high, low, volume, changes) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        curs.execute(sql, (date, t, close, op, high, low, volume, changes))
        print(date + " US10YT OK")
    
    conn.commit()
    conn.close()

# USD/KRW 원화 (환율) 세팅용 (1회)
def usd_krw():
    df = fdr.DataReader('USD/KRW', '2017-01-01')
    df.reset_index(drop = False, inplace=True)
    df = df.values.tolist()
    t =  "USD/KRW"
    for row in df:
        date = row[0].strftime("%Y-%m-%d")
        op = row[1]
        close = row[2]
        high = row[3]
        low = row[4]
        changes = row[5]

        volume = 0 # 환율은 거래량이 없다
        
        sql = "INSERT INTO daily_total (date, type, close, open, high, low, volume, changes) values(%s, %s, %s, %s, %s, %s, %s, %s)"
        curs.execute(sql, (date, t, close, op, high, low, volume, changes))
        print(date + " OK")
    
    conn.commit()
    conn.close()



