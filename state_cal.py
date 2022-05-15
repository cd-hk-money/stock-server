from datetime import datetime, timedelta
import pymysql
import csv

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="1234", db="capstone", charset="utf8")
curs = conn.cursor()
conn.commit()

# 사용 할 자료
today = datetime.today().strftime("%Y-%m-%d")
temp_list = []  
code_list = [] # 기업 코드 리스트

# 통합.csv 를 각각 분기별 데이터로 만들기
# 2021 반기보고서 -> 2021.09.30 2분기(연결X) 의 값
def temp():
    for code in code_list:
        for year in range(2015, 2022):
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

# 상장된 기업의 코드 리스트 생성
def find_code():
    sql = "select code from corp_krx"
    curs.execute(sql)
    temp = list(curs.fetchall())

    for code in temp:
        code_list.append(code[0])

find_code()

# code로 재무제표 기반 EPS, BPS, ROE 계산
def cal_statement():
    cnt = 0
    last_day = std_day()
    for code in code_list:
        sql = "SELECT sm.stocks FROM stock_marcap as sm where code like %s and date = %s"

        curs.execute(sql, (code[:5]+"%", last_day))
        datas = curs.fetchall()
        
        if len(datas) == 0:
            # 값이 안 긁히면 거래정지 or 상장폐지
            print(code + " 이 기업은 거래정지 or 상장폐지된 기업")  
            continue
        else:
            # 보통주 + 모든 우선주 주식 수
            total_stock = sum(data[0] for data in datas)
    
        # 임시 쿼리문
        sql = "SELECT ss.code, ss.date, ss.type, ss.equity, ss.equity_non, ss.profit, ss.profit_non \
                from stock_statements as ss where ss.code = %s"
        
        curs.execute(sql, code)
        temp = curs.fetchall()
        
        datas = []

        for data in temp:
            datas.append(list(data))

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
                pass
            else:
                roe = round((total_profit / ((equity + equity_prev) // 2)) * 100, 2)
            
            sql = "INSERT INTO stock_indicator_temp (code, date, type, eps, bps, roe) \
                values (%s, %s, %s, %s, %s, %s)"

            curs.execute(sql, (code, datas[i][1], datas[i][2], eps, bps, roe))
            print(code + " " + str(cnt) + " OK")
        cnt += 1
    conn.commit()
    conn.close()

# PER, PBR 계산
def every_statement():
    start = "2020-01-01"
    end = "2021-12-31"

    for code in code_list:
        
        sql = "Select * from stock_indicator_temp where code = %s and date >= '2019-01'"
        curs.execute(sql, code)
        temp = curs.fetchall()
        
        if len(temp) == 0:
            # 값이 안 긁히면 거래정지 or 상장폐지
            print(code + " 이 기업은 재무제표가 없어요 ㅠㅠ")  
            continue
        
        idc = []
        for data in temp:
            idc.append(list(data))
        
        sql = "Select sm.date, sm.close from stock_marcap as sm where code = %s and date between %s and %s"
        curs.execute(sql, (code, start, end))
        temp = curs.fetchall()
        
        marc = []
        for data in temp:
            marc.append(list(data))

        cnt = 0
        for i in range(3, len(idc)):
            eps = idc[i][3] + idc[i-1][3] + idc[i-2][3] + idc[i-3][3]
            bps = idc[i][4]
            
            idx = cnt
            for j in range(idx, len(marc)):
                if eps == 0 or bps == 0:
                    continue
                
                per = round(marc[j][1] / eps, 2)
                pbr = round(marc[j][1] / bps, 2)

                if marc[j][0][:7] > idc[i][1]:
                    break
                else:
                    sql = "UPDATE stock_marcap SET per = %s, pbr = %s where code = %s and date = %s"                        
                    curs.execute(sql, (per, pbr, code, marc[j][0]))
                    print(code + " " + marc[j][0] + " UPDATE OK")
                    cnt += 1 

    conn.commit()
    conn.close()
    
# PSR을 따로 구하자
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

# stock_marcap 테이블 + stock_indicator_day 테이블
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
            
            sql = "SELECT s.per, s.pbr from stock_indicator_day as s where code = %s and date = %s"
            curs.execute(sql, (code, date))
            temp2 = curs.fetchall()

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

            if len(temp2) == 0:
                per, pbr = 0, 0
            else:
                per, pbr = temp2[0][0], temp2[0][1]

            sql = "INSERT INTO stock_marcap (date, code, name, market, close, changes, changes_ratio, open,\
                 high, low, volume, amount, marcap, stocks, per, pbr)\
                     values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            
            curs.execute(sql, (date, code, name, market, close, changes, changes_ratio, open, high, low, volume, amount, marcap, stocks, per, pbr))
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










