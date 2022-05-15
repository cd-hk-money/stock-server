from fastapi import FastAPI
from starlette.responses import JSONResponse

import testcontroller

app = FastAPI()

#서버가 잘 붙었나 확인
@app.get("/")
async def root():
    return {"test server Ready"}

#회원 관련 API 는 Spring Server에서...
@app.post("/signup")
async def signup():
    return "signup"

@app.get("/login")
async def login():
    return "login"

#------------------------하위 주가 관련 API---------------------#
#자동완성 {코드 : 기업} (선물 X)
@app.get("/allcorps")
async def all_code():
    data = testcontroller.match_corp()
    return data
    
#자동완성 {코드 : 기업} (선물 O)
@app.get("/allkrx")
async def all_code():
    data = testcontroller.match_krx()
    return data

#KOSPI, NASDAQ, S&P500 종합 지수 + US 채권 수익률 
@app.get("/daily/total")
async def daily_total():
    data = testcontroller.find_daily_total()
    return data

#상위종목 시총, 변동률, 거래대금 TOP 50
@app.get("/daily/rank")
async def daily_rank():
    data = testcontroller.daily_rank()
    return data

#추천종목 (현재는 랜덤으로 최대 12개)
@app.get("/daily/recom")
async def daily_recommand():
    data = testcontroller.find_recommand()
    return data

#종목 검색 (기본정보)
@app.get("/stock/{name}")
async def stockinfo(name: str):
    data = testcontroller.stock_info(name)

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
        "sector": data[16]
    })

#5년 주가 데이터 (소요시간 7초)
@app.get("/stock/graph/detail/{name}")
async def detailgraph(name: str, flag: str):
    res = testcontroller.graph5year(name)
    return res

#2주 주가 데이터 (시간 벌기용)
@app.get("/stock/graph/{name}")
async def stockgraph(name: str):
    res = testcontroller.graph2weeks(name)
    return res

#날짜 지정 주가 그래프 (2017-03-30 부터 조회 가능)
@app.get("/stock/graph/{name}/{start}/{end}")
async def custom_graph(name:str, start:str, end:str):
    res = testcontroller.graph_detail(name, start, end)
    return res

#영업이익, 매출액 그래프 type 으로 구분
@app.get("/stock/statement/{type}/{name}")
async def ebitda_graph(type:str, name: str):
    res = testcontroller.type2graph(type, name)
    return res
    
#기업의 재무제표 (최근 4분기)
@app.get("/stock/statement/{name}")
async def stock_statement(name: str):
    res = testcontroller.find_statement(name)
    return res

#기업의 보조지표 EPS, BPS, ROE (최근 4분기)
@app.get("/stock/indicator/{name}")
async def stock_indicator(name:str):
    res = testcontroller.find_indicator(name)
    return res


