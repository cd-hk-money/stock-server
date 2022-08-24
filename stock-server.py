from tracemalloc import start
from fastapi import FastAPI
from starlette.responses import JSONResponse
import py_eureka_client.eureka_client as ec
import uvicorn
import asyncio
import nest_asyncio
import stockservice
import stock_news

##--------------- Eureka 설정 --------------##
# nest_asyncio.apply()

# async def set_eureka():
#     my_server_host = "127.0.0.1"
#     rest_port = 8050
#     ec.init(eureka_server="http://localhost:8761/eureka",
#             app_stock-code="stock-service",
#             instance_host=my_server_host,
#             instance_port=rest_port)

# asyncio.run(set_eureka())
# set_eureka()  
##------------------------------------------##
app = FastAPI()

#서버가 잘 붙었나 확인
@app.get("/")
async def root():
    return {"stock server Ready"}

#------------------------하위 주가 관련 API---------------------#
#자동완성 {코드 : 기업} (선물 X)
@app.get("/krx-corps")
async def all_code():
    data = stockservice.match_corp()
    return data
    
#자동완성 {코드 : 기업} (선물 O)
@app.get("/krx")
async def all_krx():
    data = stockservice.match_krx()
    return data

#KOSPI, NASDAQ, S&P500 종합 지수, US 채권 수익률, 환율(USD/KRW)
@app.get("/daily/trend")
async def daily_total():
    data = stockservice.find_daily_total()
    return data

#상위종목 시총, 변동률, 거래대금 TOP 50
@app.get("/daily/rank")
async def daily_rank():
    data = stockservice.daily_rank()
    return data

#추천종목 (현재는 랜덤으로 최대 12개)
@app.get("/daily/recommand")
async def daily_recommand():
    data = stockservice.find_recommand()
    return data

#종목 검색 (기본정보)
@app.get("/stock/{stockcode}")
async def stockinfo(stockcode: str):
    data = stockservice.stock_info(stockcode)

    return JSONResponse({
        "date": data[0],
        "code": data[1],
        "name": data[2],
        "market": data[3],
        "close": data[4],
        "changes": data[5],
        "changes_ratio": data[6],
        "open": data[7],
        "high": data[8],
        "low": data[9],
        "volume": data[10],
        "amount": data[11],
        "marcap": data[12],
        "stocks": data[13],
        "per": data[14],
        "pbr": data[15],
        "psr": data[16],
        "sector": data[17]
    })

#종목 뉴스
@app.get("/stock/{stockcode}/news")
async def stocknews(stockcode: str):
    res = stock_news.crawl_news(stockcode)
    return res

#2주 주가 데이터 (시간 벌기용)
@app.get("/stock/{stockcode}/price")
async def stockgraph(stockcode: str):
    res = stockservice.graph2weeks(stockcode)
    return res

#해당 기업 업종평균 per, pbr, psr (1년치)
@app.get("/stock/{stockcode}/sector")
async def stock_sector_pebr(stockcode:str):
    res = stockservice.sector_pebr(stockcode)
    return res

## TODO
#기업의 업종평균 EPS, BPS, ROE


#5년 주가 데이터 (소요시간 4초)
@app.get("/stock/{stockcode}/years-price")
async def detailgraph(stockcode: str):
    res = stockservice.graph5year(stockcode)
    return res

#5년 거래량 데이터 (소요시간 4초)
@app.get("/stock/{stockcode}/years-volume")
async def voulumegraph(stockcode: str):
    res = stockservice.graphvolume5year(stockcode)
    return res

#날짜 지정 주가 그래프 (2017-03-30 부터 조회 가능)
@app.get("/stock/{stockcode}/price/{start}/{end}")
async def custom_graph(stockcode:str, start:str, end:str):
    res = stockservice.graph_detail(stockcode, start, end)
    return res

#기업의 재무제표 (최근 4분기)
@app.get("/stock/{stockcode}/statement")
async def stock_statement(stockcode: str):
    res = stockservice.find_statement(stockcode)
    return res

#영업이익, 매출액 그래프 type 으로 구분
@app.get("/stock/{stockcode}/statement/{type}")
async def ebitda_graph(stockcode: str, type:str):
    res = stockservice.type2graph(type, stockcode)
    return res
    
#기업의 보조지표 EPS, BPS, ROE (최근 4분기)
@app.get("/stock/{stockcode}/indicator")
async def stock_indicator(stockcode:str):
    res = stockservice.find_indicator(stockcode)
    return res

#기업의 적정주가 (분기)
@app.get("/stock/{stockcode}/evaluation")
async def stock_evaluation(stockcode: str):
    res = stockservice.get_evalutation(stockcode)
    return res

#기업의 적정주가 (일일)
@app.get("/stock/{stockcode}/evaluation/daily")
async def stock_daily_evaluation(stockcode: str):
    res = stockservice.get_daily_evalutation(stockcode)
    return res

if __name__ == '__main__':
    uvicorn.run(app="stock-server:app", port=8080, reload=True)

