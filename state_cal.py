from datetime import datetime, timedelta
from pandas import date_range
import pymysql
import FinanceDataReader as fdr
import csv

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="1234", db="capstone", charset="utf8")
curs = conn.cursor()
conn.commit()

# 사용 할 자료
today = datetime.today().strftime("%Y-%m-%d")
temp_list = []  
code_list = [] # 기업 코드 리스트

# 상장된 기업의 코드 리스트 생성
def find_code():
    sql = "select code from corp_krx"
    curs.execute(sql)
    temp = list(curs.fetchall())

    for code in temp:
        code_list.append(code[0])

find_code()

# 연결 보고서를 각 분기별 보고서로 만들기
def report_cal():
    for code in code_list:
        for year in range(2021, 2023):
            sql = "select * from stock_statements_origin where code = %s and date like %s"

            curs.execute(sql, (code, str(year) + "%"))
            temp = list(curs.fetchall())

            datas = []
            for val in temp:
                datas.append(list(val))
            
            datas.sort(key = lambda x : x[1])

            # 분기별 값 계산
            for i in range(len(datas)-1, 0, -1):
                
                #당기순이익(지배) = 당기순이익 - 당기순이익(비지배)
                datas[i][8] -= datas[i-1][8]
                datas[i][9] -= datas[i-1][9]

                #매출액
                datas[i][10] -= datas[i-1][10]

                #영업이익
                datas[i][13] -= datas[i-1][13]

            for row in datas:

                code = row[0]
                date = row[1]
                report_type = row[2]
                asset = row[3]
                equity = row[4]
                equity_non = row[5]
                liability = row[6]
                current_asset = row[7]
                profit = row[8]
                profit_non = row[9]
                revenue = row[10]
                cash = row[11]
                depriciation = row[12]
                ebitda = row[13]
                gross_margin = row[14]

                sql = "INSERT IGNORE INTO stock_statements (code, date, type, asset, equity, equity_non, liability,\
                current_asset, profit, profit_non, revenue, cash, depriciation, ebitda, gross_margin) \
                values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

                curs.execute(sql, (code, date, report_type, asset, equity, equity_non, liability, current_asset,\
                    profit, profit_non, revenue, cash, depriciation, ebitda, gross_margin))

                print(code + " " + date + " ok")

    conn.commit()
    conn.close()

# 주말 = 주가 정보 X 따라서 가장 마지막 주가 날짜 갖고오기
def std_day():
    sql = "select s.date from stock_marcap as s ORDER BY date DESC limit 1"

    curs.execute(sql)
    data = curs.fetchall()

    return data[0][0]

# code로 재무제표 기반 EPS, BPS, ROE 계산
def cal_statement():
    cnt = 0
    last_day = std_day()
    for code in code_list:
        sql = "SELECT stocks FROM stock_marcap where code like %s and date = %s"

        curs.execute(sql, (code[:5]+"%", last_day))
        datas = curs.fetchall()

        if len(datas) == 0:
            # 값이 안 긁히면 거래정지 or 상장폐지
            print(code + " 이 기업은 거래정지 or 상장폐지된 기업")  
            continue
        else:
            # 보통주 + 모든 우선주 주식 수
            total_stock = sum(data[0] for data in datas)
    
        sql = "SELECT code, date, type, equity, equity_non, profit, profit_non \
                from stock_statements where code = %s and date >= 2020-12"
        
        curs.execute(sql, code)
        datas = list(curs.fetchall())

        datas.sort(key = lambda x : x[1], reverse=True) # 내림차순 정렬

        for i in range(len(datas)-4):
            profit = datas[i][5] - datas[i][6] #분기 당기순이익(지배)
            equity = datas[i][3] - datas[i][4] #자본총계(지배)
            equity_prev = datas[i+4][3] - datas[i+4][4] #전기 자본총계(지배) 
            total_profit = 0

            std = datas[i:i+4]
            for val in std:
                total_profit += (val[5] - val[6])

            # EPS : 당기순이익(지배) // 총 주식 수(우선주 포함)
            eps = profit // total_stock 

            # BPS : 자본총계(지배) // 총 주식 수(우선주 포함)
            bps = equity // total_stock

            # ROE : 당기순이익(연결) // (자본총계(당기) + 자본총계(전기)) / 2 X 100
            if equity == 0 and equity_prev == 0:
                roe = 0
            else:
                roe = round((total_profit / ((equity + equity_prev) // 2)) * 100, 2)
            
            sql = "INSERT IGNORE INTO stock_indicator (code, date, type, eps, bps, roe) \
                values (%s, %s, %s, %s, %s, %s)"

            curs.execute(sql, (code, datas[i][1], datas[i][2], eps, bps, roe))
            print(code + " " + str(cnt) + " OK")
        cnt += 1

    conn.commit()
    conn.close()

# PER, PBR 계산
def pebr_statement():
    for code in code_list:
        sql = "Select date, eps, bps from stock_indicator where code = %s"
        curs.execute(sql, code)
        indi = list(curs.fetchall())

        if len(indi) == 0:
            # 값이 안 긁히면 거래정지 or 상장폐지
            print(code + " 이 기업은 재무제표가 없어요 ㅠㅠ")  
            continue
    
        for i in range(3, len(indi)):
            start = indi[i-1][0] + "-31"
            end = indi[i][0] + "-31"     
            sql = "Select date, close, marcap from stock_marcap where code = %s and date between %s and %s"
            print(start, end)

            curs.execute(sql, (code, start, end))
            marcaps = list(curs.fetchall())
        
            #계산에 사용할 eps, bps
            eps = indi[i][1] + indi[i-1][1] + indi[i-2][1] + indi[i-3][1]
            bps = indi[i][2]
            
            if eps == 0 or bps == 0:
                continue
                
            for date, close, marcap in marcaps:
                per = round(close / eps, 1)
                pbr = round(close / bps, 1)

                sql = "UPDATE stock_marcap SET per = %s, pbr = %s where code = %s and date = %s"                        
                curs.execute(sql, (per, pbr, code, date))
                print(code + " " + date + " UPDATE OK")

    conn.commit()
    conn.close()

# PER, PBR, PSR 업데이트용
def every_pebr():
    start = "2022-07-02"
    end = "2022-07-06"
    
    for code in code_list:
        # 마지막 재무제표에서 EPS, BPS 뽑아오기 
        sql = "Select eps, bps from stock_indicator where code = %s ORDER BY date DESC limit 4"
        curs.execute(sql, code)
        temp = curs.fetchall()
        
        if len(temp) == 0:
            print(code + " 이 기업은 재무제표가 없습니다 ...")
            continue
        else:
            eps = sum(val[0] for val in temp)
            bps = temp[0][1]

        # 마지막 재무제표에서 매출액 뽑아오기
        sql = "Select revenue from stock_statements where code = %s and date = '2022-03'"
        curs.execute(sql, code)
        temp = curs.fetchall()
        
        if len(temp) == 0:
            print(code + " 이 기업의 마지막 재무제표는 매출액이 없어요")
            rev = 0
        else:
            rev = temp[0][0]

        # 종가, 시총 뽑아오기
        sql = "Select date, close, marcap from stock_marcap where code = %s and date between %s and %s"
        curs.execute(sql, (code, start, end))
        temp = curs.fetchall()
        temp = list(temp)
        
        # PER, PBR, PSR 한번에 우겨넣기
        if len(temp) == 0:
            print(code + " 거래중지가 된 기업입니다.")
        else:
            for date, close, marcap in temp:
                per = close / eps if eps != 0 else 0
                pbr = close / bps if bps != 0 else 0
                psr = marcap / rev if rev != 0 else 0
                sql = "Update stock_marcap SET per = %s, pbr = %s, psr = %s where code = %s and date = %s"
                curs.execute(sql, (per, pbr, psr, code, date))
                
                print(code + " " + date + " OK")
    
    conn.commit()
    conn.close()


# PSR 계산
def psr_statement():
    start = "2020-01-01"
    end = "2021-09-30"
    
    for code in code_list:
        sql = "select date, revenue from stock_statements where code = %s and date > 2020-01"
        curs.execute(sql, code)
        temp = curs.fetchall()
        
        if len(temp) == 0:
            print("재무제표가 없어요 ㅠㅠ")
        
        rev = []
        for data in temp:
            rev.append(data)
        
        
        sql = "select date, marcap from stock_marcap where code = %s and date between %s and %s"
        curs.execute(sql, (code, start, end))
        temp = curs.fetchall()
        
        if len(temp) == 0:
            print("2020년 이전에 상장폐지 했어요")
        
        marc = []
        for data in temp:
            marc.append(data)
        
        cnt = 0 #날짜 카운트용
        for revenue in rev:
            idx = cnt
            for i in range(idx, len(marc)):
                if marc[i][0][:7] > revenue[0]:
                    break
                
                if revenue[1] != 0:
                    psr = marc[i][1] / revenue[1]
                else:
                    psr = 0
            
                sql = "UPDATE stock_marcap SET psr = %s where code = %s and date = %s"
                curs.execute(sql, (psr, code, marc[i][0]))
                print(code + " " + marc[i][0] + " OK")
                cnt += 1
        
    conn.commit()
    conn.close()
    
# stock_marcap 테이블
# 무식한 ver
def union_table():
    sql = "SELECT distinct code FROM stock_marcap_old"
    curs.execute(sql)
    temp = curs.fetchall()

    codes = []
    for data in temp:
        codes.append(data[0])

    start = datetime.strptime(std_day(), "%Y-%m-%d").date() + timedelta(days=1)
    end = datetime.strptime(today, "%Y-%m-%d").date()
    
    dates = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end-start).days+1)]
    cnt = 0
    for code in codes:
        for date in dates:
            sql = "SELECT * from stock_marcap_old where code = %s and date = %s"

            curs.execute(sql, (code, date))
            temp = curs.fetchall()

            if len(temp) == 0: 
                print("주말 or 자연재해") 
                continue

            name = temp[0][2]
            market = temp[0][3]
            close = temp[0][4]
            changes = temp[0][5]
            changes_ratio = temp[0][6]
            open = temp[0][7]
            high = temp[0][8]
            low = temp[0][9]
            volume = temp[0][10]
            amount = temp[0][11]
            marcap = temp[0][12]
            stocks = temp[0][13]


            per, pbr, psr = 0, 0, 0


            sql = "INSERT INTO stock_marcap (date, code, name, market, close, changes, changes_ratio, open,\
                 high, low, volume, amount, marcap, stocks, per, pbr, psr)\
                     values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            
            curs.execute(sql, (date, code, name, market, close, changes, changes_ratio, open, high, low, volume, amount, marcap, stocks, per, pbr, psr))
            print(date + " " + code + " " + str(cnt) + " OK")
        cnt += 1
    conn.commit()
    conn.close()

#daily_total 전용 마지막 날짜 구하기
def total_day():
    sql = "select s.date from daily_total as s ORDER BY date DESC limit 1"

    curs.execute(sql)
    data = curs.fetchall()

    return data[0][0]

# 업종 평균 PER, PBR, PSR 초회 세팅용
def sector_pebr():
    krx = fdr.StockListing('KRX')
    temp = krx.drop(['Symbol', 'Market', 'Name', 'Industry', 'ListingDate', 'SettleMonth', 'Representative', 'HomePage', 'Region'], axis=1)
    temp = temp.groupby('Sector').count()

    sector_list = list(temp.index.values)

    start = datetime.strptime("2022-05-28", "%Y-%m-%d")
    end = datetime.strptime("2022-07-06", "%Y-%m-%d")
    # date = std_day()
    # 161개의 업종을 하나씩 순회
    for sector in sector_list:
        data = krx[krx['Sector'] == sector]['Symbol']
        for date in date_range(start, end):
            date = datetime.strftime(date, "%Y-%m-%d")

            per, pbr, psr = 0, 0, 0
            # 업종에 속한 모든 기업을 순회
            for code in data:
                # 업종 평균 PER, PBR, PSR 을 구하려면 쿼리문이 이게 최선일까?
                sql = "select per, pbr, psr from stock_marcap where code = %s and date = %s"
                curs.execute(sql, (code, date))
                temp = curs.fetchall()
                
                temp = list(temp)
                if len(temp) == 0:
                    continue
                
                e, b, s = temp[0][0], temp[0][1], temp[0][2]
                
                per += e
                pbr += b
                psr += s if s != None else 0
            
            
            per /= len(data)
            pbr /= len(data)
            psr /= len(data)
            
            if per == 0 and pbr == 0 and psr == 0:
                continue
            
            sql = "INSERT INTO stock_sector (date, sector, sector_per, sector_pbr, sector_psr) values (%s, %s, %s, %s, %s)"
            # sql = "UPDATE stock_sector SET sector_per = %s, sector_pbr = %s, sector_psr = %s where date = %s and sector = %s"
            curs.execute(sql, (date, sector, per, pbr, psr))
            print(sector, date, " OK")
            
    conn.commit()
    conn.close()

# EPS 증가율 계산
def cal_epsRate():
    for code in code_list:
        sql = "select date, eps from stock_indicator where code = %s"
        curs.execute(sql, code)
        datas = list(curs.fetchall())
        
        for i in range(1, len(datas)):
            if datas[i][1] == 0 or datas[i-1][1] == 0:
                print(code + " EPS is zero")
                continue
            eps_rate = round(((datas[i][1] - datas[i-1][1]) / datas[i-1][1]) * 100, 1)
            date = datas[i][0]
            sql = "UPDATE stock_indicator SET eps_increase = %s where code = %s and date = %s"
            curs.execute(sql, (eps_rate, code, date))

        print(code + " is OK")
    
    conn.commit()
    conn.close()

# PEGR 계산
def cal_pegr():
    for code in code_list:
        sql = "select date, eps_increase from stock_indicator where code = %s"    
        curs.execute(sql, code)
        datas = list(curs.fetchall())[1:]
        
        if len(datas) == 0:
            print("재무제표가 없는 기업입니다")
            continue
            
        for data in datas:
            date = data[0] + "-31"
            sql = "select per from stock_marcap where code = %s and date <= %s ORDER BY date DESC limit 1"

            curs.execute(sql, (code, date))
            temp = list(curs.fetchall())

            if len(temp) == 0:
                print("per이 없어용")
                continue

            per = temp[0][0]

            if per == 0 or data[1] == 0:
                print("zero can't division")
                continue

            pegr = round(per / data[1], 1)

            sql = "UPDATE stock_indicator SET pegr = %s where code = %s and date = %s"
            curs.execute(sql, (pegr, code, data[0]))
            
        print(code + " is OK")

    conn.commit()
    conn.close()



                 
