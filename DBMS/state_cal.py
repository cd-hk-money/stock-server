from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta as rt
from pandas import date_range
import FinanceDataReader as fdr
import csv, db, sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from service import stockservice

conn = db.engine.connect()

# 사용 할 자료
today = datetime.today().strftime("%Y-%m-%d")
temp_list = []  
code_list = [] # 기업 코드 리스트

# 상장된 기업의 코드 리스트 생성
def find_code():
    sql = "select code from corp_krx"
    temp = list(conn.execute(sql).fetchall())

    for code in temp:
        code_list.append(code[0])

find_code()

# 연결 보고서를 각 분기별 보고서로 만들기
def report_cal():
    for code in code_list:
        for year in range(2022, 2023):
            sql = "select * from stock_statements_origin where code = %s and date like %s"

            temp = conn.execute(sql, (code, str(year) + "%")).fetchall()
            # temp = list(conn.execute(sql).fetchall())

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

                conn.execute(sql, (code, date, report_type, asset, equity, equity_non, liability, current_asset,\
                    profit, profit_non, revenue, cash, depriciation, ebitda, gross_margin))

                print(code + " " + date + " ok")

    # conn.commit()
    conn.close()

# 주말 = 주가 정보 X 따라서 가장 마지막 주가 날짜 갖고오기
def std_day():
    sql = "select s.date from stock_marcap as s ORDER BY date DESC limit 1"

    data = conn.execute(sql).fetchall()

    return data[0][0]

#특정 보조지표 업데이트를 위한 날짜 계산기
def check_date():
    f = open("marcap_" + datetime.now().strftime('%Y-%m-%d') + ".csv", 'r', encoding="UTF-8")
    cr = csv.reader(f)
    
    for row in cr:
        if row[1] == "Code":
            continue
        last_update = row[0]
        break

    return last_update

# code로 재무제표 기반 EPS, BPS, ROE 계산
def cal_statement():
    cnt = 0
    last_day = std_day()
    for code in code_list:
        sql = "SELECT stocks FROM stock_marcap where code like %s and date = %s"

        datas = conn.execute(sql, (code[:5]+"%", last_day)).fetchall()

        if len(datas) == 0:
            # 값이 안 긁히면 거래정지 or 상장폐지
            print(code + " 이 기업은 거래정지 or 상장폐지된 기업")  
            continue
        else:
            # 보통주 + 모든 우선주 주식 수
            total_stock = sum(data[0] for data in datas)
    
        sql = "SELECT code, date, type, equity, equity_non, profit, profit_non \
                from stock_statements where code = %s and date >= 2021-09"
        
        datas = list(conn.execute(sql, code).fetchall())

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

            conn.execute(sql, (code, datas[i][1], datas[i][2], eps, bps, roe))
            print(code + " " + str(cnt) + " OK")
        cnt += 1

    # conn.commit()
    conn.close()

# PER, PBR 계산
def pebr_statement():
    for code in code_list:
        sql = "Select date, eps, bps from stock_indicator where code = %s limit 4"
        indi = list(conn.execute(sql, code).fetchall())

        if len(indi) == 0:
            # 값이 안 긁히면 거래정지 or 상장폐지
            print(code + " 이 기업은 재무제표가 없어요 ㅠㅠ")  
            continue
    
        for i in range(3, len(indi)):
            start = indi[i-1][0] + "-31"
            end = indi[i][0] + "-31"     
            sql = "Select date, close, marcap from stock_marcap where code = %s and date between %s and %s"
            print(start, end)

            marcaps = list(conn.execute(sql, (code, start, end)).fetchall())
        
            #계산에 사용할 eps, bps
            eps = indi[i][1] + indi[i-1][1] + indi[i-2][1] + indi[i-3][1]
            bps = indi[i][2]
            
            if eps == 0 or bps == 0:
                continue
                
            for date, close, marcap in marcaps:
                per = round(close / eps, 1)
                pbr = round(close / bps, 1)

                sql = "UPDATE stock_marcap SET per = %s, pbr = %s where code = %s and date = %s"                        
                conn.execute(sql, (per, pbr, code, date))
                print(code + " " + date + " UPDATE OK")

    # conn.commit()
    conn.close()

# PER, PBR, PSR 업데이트용
def every_pebr():
    start = check_date()
    end = std_day()
    # start = "2022-06-01"
    # end = std_day()

    for code in code_list:
        # 마지막 재무제표에서 EPS, BPS 뽑아오기 
        sql = "Select eps, bps from stock_indicator where code = %s ORDER BY date DESC limit 4"
        temp = conn.execute(sql, code).fetchall()
        
        if len(temp) == 0:
            print(code + " 이 기업은 재무제표가 없습니다 ...")
            continue
        else:
            eps = sum(val[0] for val in temp)
            bps = temp[0][1]

        # 마지막 재무제표에서 매출액 뽑아오기
        sql = "Select revenue from stock_statements where code = %s order by date DESC limit 1"
        temp = conn.execute(sql, code).fetchall()
        
        if len(temp) == 0:
            print(code + " 이 기업의 마지막 재무제표는 매출액이 없어요")
            rev = 0
        else:
            rev = temp[0][0]

        # 종가, 시총 뽑아오기
        sql = "Select date, close, marcap from stock_marcap where code = %s and date between %s and %s"
        temp = conn.execute(sql, (code, start, end)).fetchall()
        temp = list(temp)
        
        # PER, PBR, PSR 한번에 우겨넣기
        if len(temp) == 0:
            print(code + " 거래중지가 된 기업 or 재무제표가 없습니다 .")
        else:
            for date, close, marcap in temp:
                per = close / eps if eps != 0 else 0
                pbr = close / bps if bps != 0 else 0
                psr = marcap / rev if rev != 0 else 0
                sql = "Update stock_marcap SET per = %s, pbr = %s, psr = %s where code = %s and date = %s"
                conn.execute(sql, (per, pbr, psr, code, date))
                
                print(code + " " + date + " OK")
    
    # conn.commit()
    conn.close()


# PSR 계산
def psr_statement():
    start = "2020-01-01"
    end = "2021-09-30"
    
    for code in code_list:
        sql = "select date, revenue from stock_statements where code = %s and date > 2020-01"
        temp = conn.execute(sql, code).fetchall()
        
        if len(temp) == 0:
            print("재무제표가 없어요 ㅠㅠ")
        
        rev = []
        for data in temp:
            rev.append(data)
        
        
        sql = "select date, marcap from stock_marcap where code = %s and date between %s and %s"
        temp = conn.execute(sql, (code, start, end)).fetchall()
        
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
                conn.execute(sql, (psr, code, marc[i][0]))
                print(code + " " + marc[i][0] + " OK")
                cnt += 1
        
    # conn.commit()
    conn.close()
    
# stock_marcap 테이블
# 무식한 ver
def union_table():
    sql = "SELECT distinct code FROM stock_marcap_old"
    temp = conn.execute(sql).fetchall()

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

            temp = conn.execute(sql, (code, date)).fetchall()

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

            sql = "INSERT IGNORE INTO stock_marcap (date, code, name, market, close, changes, changes_ratio, open,\
                 high, low, volume, amount, marcap, stocks, per, pbr, psr)\
                     values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            
            conn.execute(sql, (date, code, name, market, close, changes, changes_ratio, open, high, low, volume, amount, marcap, stocks, per, pbr, psr))
            print(date + " " + code + " " + str(cnt) + " OK")
        cnt += 1
    # conn.commit()
    conn.close()

#daily_total 전용 마지막 날짜 구하기
def total_day():
    sql = "select s.date from daily_total as s ORDER BY date DESC limit 1"

    data = conn.execute(sql).fetchall()

    return data[0][0]

# 업종 리스트 가져오기
def sectorList():
    sql = "select distinct sector from corp_krx"
    data = conn.execute(sql).fetchall()

    return data

def sectorCodes(sector):
    sql = "select distinct code from corp_krx where sector = %s"
    data = conn.execute(sql, sector).fetchall()

    return data

# 업종 평균 PER, PBR, PSR 초회 세팅용
def sector_pebr():
    allsector = sectorList()
    start = check_date()
    end = std_day()
    
    # 161개의 업종을 하나씩 순회
    for sector in allsector:
        data = sectorCodes(sector[0])
        for date in date_range(start, end):
            date = datetime.strftime(date, "%Y-%m-%d")

            per, pbr, psr = 0, 0, 0
            # 업종에 속한 모든 기업을 순회
            for code in data:
                # 업종 평균 PER, PBR, PSR 을 구하려면 쿼리문이 이게 최선일까?
                sql = "select per, pbr, psr from stock_marcap where code = %s and date = %s"
                temp = conn.execute(sql, (code[0], date)).fetchall()
                
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
            
            # sql = "INSERT INTO stock_sector_daily (date, sector, sector_per, sector_pbr, sector_psr) values (%s, %s, %s, %s, %s)"
            sql = "UPDATE stock_sector_daily SET sector_per = %s, sector_pbr = %s, sector_psr = %s where date = %s and sector = %s"
            conn.execute(sql, (per, pbr, psr, date, sector[0]))
            print(sector, date, " OK")
            
    # conn.commit()
    conn.close()

#업종평균 EPS, BPS, ROE (최적화 필요)
def sector_indicator():
    sector_list = sectorList()

    for sector in sector_list:
        data = sectorCodes(sector[0])  
        start = datetime.strptime("2022-06", "%Y-%m")
        end = datetime.strptime("2022-09", "%Y-%m")

        eps, bps, roe = 0, 0, 0

        while start <= end: 
            std = start.strftime("%Y-%m")
            N = len(data)
            for code in data:
                sql = "select eps, bps, roe from stock_indicator where code = %s and date = %s"
                q = list(conn.execute(sql, (code[0], std)).fetchall())

                if len(q) == 0:
                    N -= 1
                    continue

                eps += q[0][0]
                bps += q[0][1]
                roe += q[0][2]
            
            if N != 0:
                eps = round(eps/N, 2)
                bps = round(bps/N, 2)
                roe = round(roe/N, 2)
            
            sql = "INSERT INTO stock_sector (date, sector, sector_eps, sector_bps, sector_roe) values (%s, %s, %s, %s, %s)"
            # sql = "UPDATE stock_sector SET sector_eps = %s, sector_bps = %s, sector_roe = %s where date = %s and sector = %s"
            # conn.execute(sql, (eps, bps, roe, std, sector[0]))
            conn.execute(sql, (std, sector[0], eps, bps, roe))
            print(sector[0] + " OK")
            start += rt(months=3)
    
    # conn.commit()
    conn.close()

# EPS 증가율 계산
def cal_epsrate():
    for code in code_list:
        sql = "select date, eps from stock_indicator where code = %s order by date DESC limit 4"
        datas = list(conn.execute(sql, code).fetchall())
        
        for i in range(len(datas)-1, 0, -1):
            if datas[i][1] == 0 or datas[i-1][1] == 0:
                print(code + " EPS is zero")
                continue

            eps_rate = round(((datas[i-1][1] - datas[i][1]) / datas[i][1]) * 100, 1)
            date = datas[i-1][0]
            sql = "UPDATE stock_indicator SET eps_increase = %s where code = %s and date = %s"
            conn.execute(sql, (eps_rate, code, date))

        print(code + " is OK")
    
    # conn.commit()
    conn.close()

# PEGR 계산
def cal_pegr():
    for code in code_list:
        sql = "select date, eps_increase from stock_indicator where code = %s"    
        datas = list(conn.execute(sql, code).fetchall())[-3:]
        
        if len(datas) == 0:
            print("재무제표가 없는 기업입니다")
            continue
            
        for data in datas:
            date = data[0] + "-31"
            sql = "select per from stock_marcap where code = %s and date <= %s ORDER BY date DESC limit 1"

            temp = list(conn.execute(sql, (code, date)).fetchall())

            if len(temp) == 0:
                print("per이 없습니다")
                continue

            per = temp[0][0]

            if per == 0 or data[1] == 0:
                print("zero can't division")
                continue

            pegr = round(per / data[1], 1)

            sql = "UPDATE stock_indicator SET pegr = %s where code = %s and date = %s"
            conn.execute(sql, (pegr, code, data[0]))
            
        print(code + " is OK")

    # conn.commit()
    conn.close()

# 적정주가 (분기) 계산
def cal_evalu():
    for code in code_list:
        sql = "select date, eps, roe from stock_indicator where code = %s ORDER BY date"
        datas = conn.execute(sql, code).fetchall()

        if len(datas) == 0:
            print("잘못된 기업명 or 데이터가 없다")
            continue
        
        for i in range(3, len(datas)):
            eps = datas[i][1] + datas[i-1][1] + datas[i-2][1] + datas[i-3][1]
            roe = datas[i][2]

            if datas[i-3][2] < datas[i-2][2] < datas[i-1][2]: # ROE 가 3년연속 상승 이라면?
                s_rim_roe = datas[i][2]
            elif datas[i-3][2] > datas[i-2][2] > datas[i-1][2]: # 3년 연속 하라이라면?
                s_rim_roe = datas[i][2]
            else:
                s_rim_roe = round((datas[i-3][2] + (datas[i-2][2] * 2) + (datas[i-1][2] * 3)) / 6, 2)

            eval1 = round(eps * roe)
                    
            # S-Rim 적정주가
            sql = "select equity, equity_non from stock_statements where code = %s and date = %s"
            datas2 = conn.execute(sql,  (code, datas[i][0])).fetchall()

            equity = datas2[0][0] - datas2[0][1] # 자본총계 (지배)
            rate = 10.2 # 한국 신용평가의 BBB- 등급 채권의 5년 수익률 
            
            # 보통주 + 우선주
            sql = "select stocks from stock_marcap where code like %s and date = %s"
            datas3 = conn.execute(sql, (code[:5]+"%", stockservice.last_day)).fetchall()

            if len(datas3) == 0:
                # 값이 안 긁히면 거래정지 or 상장폐지
                print(code + " 이 기업은 거래정지 or 상장폐지된 기업")
                continue  
            else:
                # 보통주 + 모든 우선주 주식 수
                total_stock = sum(data[0] for data in datas3)

            eval2 = round((equity * (s_rim_roe / rate)) / total_stock)

            sql = "update stock_indicator set proper_price = %s, s_rim = %s where code = %s and date = %s"
            conn.execute(sql, (eval1, eval2, code, datas[i][0]))
    
    conn.close()

#적정주가 일일 계산 초회 세팅용 (+ 재무재표가 추가된다면)
# 계산식 : EPS * PBR/PER
def cal_daily_evalu():
    for code in code_list:
        sql = "select date, eps from stock_indicator where code = %s ORDER BY date"
        datas = conn.execute(sql, code).fetchall()

        if len(datas) == 0:
            print("잘못된 기업명 or 데이터가 없다")
            continue
        
        #EPS는 1년간의 연속된 값을 사용한다, 근데 날짜 계산이 빡센..
        for i in range(3, len(datas)-1):
            eps = datas[i][1] + datas[i-1][1] + datas[i-2][1] + datas[i-3][1]
            
            #EPS 와 같은 기간의 PER, PBR을 읽어오자
            start = datas[i][0] + "-01"
            end = datas[i+1][0] + "-00"

            sql = "select date, per, pbr from stock_marcap where code = %s and date between %s and %s"
            datas2 = list(conn.execute(sql, (code, start, end)).fetchall())

            for data in datas2:
                if data[2] == 0 or data[1] == 0:
                    print("계산할 수 없습니다. can't devide zero ")
                    continue

                v = round(eps * ((data[2] / data[1]) * 100))

                sql = "INSERT INTO daily_evaluation (date, code, daily_proper_price) values(%s, %s, %s)"
                conn.execute(sql, (data[0], code, v))
            
            # conn.commit()
        
        #일단 최근자의 예측을 위해 마지막 재무제표 기준 계산
        if len(datas) >= 4:
            eps = datas[-1][1] + datas[-2][1] + datas[-3][1] + datas[-4][1]
            start = datas[-1][0] + "-01" 
            end = std_day()

            sql = "select date, per, pbr from stock_marcap where code = %s and date between %s and %s"
            datas3 = list(conn.execute(sql, (code, start, end)).fetchall())
            
            for data in datas3:
                if data[2] == 0 or data[1] == 0:
                        print("계산할 수 없습니다. can't devide zero ")
                        continue

                v = eps * ((data[2] / data[1]) * 100)
                sql = "INSERT INTO daily_evaluation (date, code, daily_proper_price) values(%s, %s, %s)"
                conn.execute(sql, (data[0], code, v))
                print(data[0] + " " + code + " OK")

            # conn.commit()
        else:
            print("최근 1년치의 EPS가 없어 계산 불가")

# 적정주가 마지막 업데이트 날짜
def evalu_lastday(code):
    sql = "select date from daily_evalutation where code = %s order by date DESC limit 1"
    data = conn.execute(sql, code).fetchall()

    if len(data) == 0:
        return False

    date = datetime.strptime(data[0][0], "%Y-%m-%d")
    date += timedelta(days=1)

    return datetime.strftime(date, "%Y-%m-%d") 

# 일일 적정주가 업데이트용 
def daily_evalu_update():
    for code in code_list:
        sql = "select date, eps from stock_indicator where code = %s and date <= '2022-06' limit 4"
        datas = conn.execute(sql, code).fetchall()

        #1년치 재무제표가 없다면 구할 수 없다.
        if len(datas) < 4:
            print("잘못된 기업명 or 데이터가 없다", code)
            continue

        eps = datas[3][1] + datas[2][1] + datas[1][1] + datas[0][1]
            
        #업데이트할 날짜 범위를 구하자
        tmp = evalu_lastday(code)
        if tmp == False:
            continue
        start = "2022-09-01"
        end = std_day()

        sql = "select date, per, pbr from stock_marcap where code = %s and date between %s and %s"
        datas2 = list(conn.execute(sql, (code, start, end)).fetchall())

        for data in datas2:
            if data[2] == 0 or data[1] == 0:
                print("계산할 수 없습니다. can't devide zero ")
                continue

            v = round((eps * (data[2] / data[1])) * 100)

            sql = "INSERT INTO daily_evalutation (date, code, daily_proper_price, evalutation_score, donda_score) values(%s, %s, %s, %s, %s) \
            ON DUPLICATE KEY UPDATE daily_proper_price = %s, evalutation_score = %s, donda_score = 0"
            # sql = "UPDATE daily_evalutation SET daily_proper_price = %s, evalutation_score= %s where date = %s and code = %s"
            conn.execute(sql, (data[0], code, v, 0, 0, v, 0))
            # conn.commit()

        print(code + "is OK")

# 돈다지수 초회 세팅 (구현은 O)
def daily_donda():
    for code in code_list:
        sql = "select date, proper_price, s_rim from stock_indicator where code = %s and proper_price != 0 order by date ASC"
        datas = conn.execute(sql, code).fetchall()

        n = len(datas)
        #1년치 미만은 계산 X
        if n < 4:
            print("이 기업은 1년 미만의 데이터를 갖고 있습니다")
            continue
        
        #분기에 해당하는 일일 적정주가 가져오기
        for i in range(1, n):
            start = datas[i-1][0] + "-01" 
            end = datas[i][0] + "-01" if i != n-1 else std_day()

            value = datas[i-1][1] + datas[i-1][2]

            sql = "select date, daily_proper_price from daily_evalutation where code = %s and date between %s and %s"
            datas2 = conn.execute(sql, (code, start, end)).fetchall()
            
            for date, daily_p in datas2:
                donda = round((value + daily_p) / 3) # 평균 낸 돈다지수

                # sql = "UPDATE daily_evalutation SET donda_score = %s where code = %s and date = %s" 
                # conn.execute(sql, (donda, code, date))
                print(date, donda)
        
        print(code + " is OK")
    
# 일일 적정주가와 현재주가를 비교, 계산
def daily_evalu_score():
    for code in code_list:
        # sql = "select date, daily_proper_price from daily_evalutation where code = %s and evalutation_score = 0 order by date"
        sql = "select date, daily_proper_price from daily_evalutation where code = %s and date between '2022-09-01' and '2022-11-04'"
        datas = list(conn.execute(sql, code).fetchall())

        if len(datas) == 0:
            print(code + " 이 종목은 데이터가 없습니다")
            continue

        start = datas[0][0]
        end = datas[-1][0]

        sql = "select date, close from stock_marcap where code = %s and date between %s and %s"
        datas2 = list(conn.execute(sql, (code, start, end)).fetchall())

        for value in zip(datas, datas2):
            v1, v2 = value[0][1], value[1][1]
            date = value[0][0]

            #(현재주가 / 적정주가) 1 보다 작으면 고평가, 크면 저평가
            if v1 == 0 or v2 == 0:
                print(code + " 적정주가가 0이여서 계산불가")
                continue
        
            v = round(v2 / v1, 2)
            v = (1-v) * -100
            sql = 'UPDATE daily_evalutation SET evalutation_score = %s where date = %s and code = %s'
            conn.execute(sql, (v, date, code))
            # conn.commit()
            
        print(code + "OK")
