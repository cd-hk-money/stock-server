import dataToDb
import state_cal

# 미리 해야 하는 것
# 0. dataToDb, state_cal 파일의 library 중 불 꺼진 library install 해주세요... (ex. schedule)
# 1. /marcap 디렉토리를 git pull을 통해 최신화 해주세요. (서버를 띄워야 자동화라 잠궈놨습니다)
# 2. fdr 라이브러리를 최신화 해주세요(중요) "pip install --upgrade finance-datareader"

# 0. US채권(1,5,10) 수익률 세팅, 1회 실시 후 daily_total() 로 최신화하면 됩니다
# dataToDb.us_bond()

# 1. 일일 주가 최신화, stock_marcap_old, stock_marcap 2개 DB UPDATE
# dataToDb.every_do()
# dataToDb.every_marcap()
# state_cal.union_table()

# 2. 일일 종합 지수 최신화 (KOSPI, NASDAQ, S&P500, US채권)
# dataToDb.daily_total()



