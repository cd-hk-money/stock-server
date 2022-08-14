import dataToDb
import state_cal
import pymysql

# 미리 해야 하는 것
# 0. dataToDb, state_cal 파일의 library 중 불 꺼진 library install 해주세요... (ex. schedule)
# 1. fdr 라이브러리를 최신화 해주세요(중요) "pip install --upgrade finance-datareader"

# 0. US채권(1,5,10) 수익률 세팅, 1회 실시 후 daily_total() 로 최신화하면 됩니다
# dataToDb.us_bond()

# 1. 일일 주가 최신화, stock_marcap_old, stock_marcap 2개 DB UPDATE
# dataToDb.every_do()
# state_cal.union_table()

# 2. 일일 종합 지수 최신화 (KOSPI, NASDAQ, S&P500, US채권)
# dataToDb.daily_total()

# 3. 매일 갱신해야 하는 메소드지만 아직 불안정한 것들
# state_cal.every_pebr() # 오늘날짜까지 per, pbr, psr update
# state_cal.sector_pebr() # 이 메소드는 수동으로 날짜를 조절하는중.... 속상하다
 