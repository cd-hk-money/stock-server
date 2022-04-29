# TEST SERVER 가이드라인

## 파일별 용도
1. testserver.py = api 매핑
2. testcontroller.py = DB와 conn
3. process_data.py = 데이터 가공

## 사용법
### 1. fastapi, uvicorn install
```
pip install fastapi
pip install uvicorn[standard]
```

### 2. 터미널에서 서버 실행
```
uvicorn testserver:app --reload --host=주소 --port=포트번호
```

### + 만약 uvicorn 명령어가 없다고 한다면?
```
python -m uvicorn testserver:app --reload --host=주소 --port=포트번호
```

### 옵션
```
--reload : 코드 변경 감지
--host : 주소 설정
--port : 포트 설정

default host = 127.0.0.1 port = 8000
```
### 3. testcontroller.py 에서 DB명 맞춰주기
![image](https://user-images.githubusercontent.com/76652908/165924330-549529b7-aeec-4710-8115-2227423aba64.png) \
MYSQL로 진행해야 하며 DB명 바꿀 때 db = "capstone" 값 수정하면 됩니다.  

## API 설계 (회원 관련 API X, 전부 GET 요청)
### 메인페이지
#### 1. 자동완성
```
/api/allcorps : 상장된 "기업" 
/api/allkrx : 상장된 기업 + 선물
```
#### 2. KOSPI, NASDAQ, S&P500 종합 지수
```
/api/daily/total
```

#### 3. 시총, 변동률, 거래대금 TOP 10
```
/api/daily/rank
```

#### 4. 추천종목 (최대 12개 랜덤)
```
/api/daily/recom
```

#### 5. 종목 검색
```
/api/stock/{name} : 기본정보 (최근 시가, 종가, 시총 등등..)
/api/stock/graph/{name} : 2주 주가 데이터 (날짜 : 종가)
/api/stock_graph/{name}/{flag} : 5년치 주가 데이터 (날짜 : 종가) flag = 아무 문자 입력
/api/stock/graph/{name}/{start}/{end} : 커스텀 날짜 데이터, 2017-03-30 ~ 2022-04-27 이내에서 가능
/api/stock/statement/{name} : 최근 4분기 재무제표 데이터
/api/stock/indicator/{name} : 최근 4분기 보조지표(EPS, BPS, ROE) 데이터 + 가장 최근 per, pbr 인데 ... 현재는 0 
/api/stock/graph/{type}/{name} : 영업이익, 매출액 그래프용 5년치 데이터 type = ebitda, revenue 둘 중 하나. 

