# 돈다 주가 API 서버

### 개요
    - KOSPI, NASDAQ, S&P500, KRW/USD 주요 시장지표 업데이트, 제공
    - 매일 KOSPI 상장된 기업의 종가 및 가격지표, 보조지표 업데이트, 제공
    - 종목 재무제표와 가격지표를 활용한 보조지표, 평가지수 제공
    - 종목의 뉴스 제공
---
### 구조
    Capstone_data
    ├─ DBMS # 주가 데이터베이스 업데이트
    │  ├─ __init__.py
    │  ├─ dataToDb.py
    │  ├─ db.py
    │  ├─ dbupdate.py
    │  └─ state_cal.py
    ├─ ml # 평가지수 계산 머신러닝
    │  ├─ __init__.py
    │  └─ donda.py
    ├─ model # 모델
    │  └─ tmp_checkpoint.h5
    ├─ service # 서비스
    │  ├─ __init__.py
    │  ├─ process_data.py
    │  ├─ stocknews.py
    │  └─ stockservice.py
    └─ stockmain.py
---
### API 설계
#### 시장지표 및 기본
    /krx-corps : 검색 자동완성 (코드 <-> 기업)
    /daily/trend : KOSPI, NASDQ, S&P500, KRW/USD 종합 지수
    /daily/rank : 시총, 변동률, 거래량 TOP 50
    /daily/recommand : 평가지수 기반 저평가 기업 12개
#### 종목 기본정보
    /stock/{종목코드} : 종목검색
    /stock/{종목코드}/price : 종목의 2주 종가
    /stock/{종목코드}/news : 종목 관련 뉴스
    /stock/{종목코드}/similar : 같은 업종의 종목정보 제공
#### 종목 상세정보 (재무재표, 보조지표)
    /stock/{종목코드}/indicator : 종목 EPS, BPS, ROE
    /stock/{종목코드}/indicator/daily : 종목 PER, PBR, PSR
    
    /stock/{종목코드}/sector : 종목 업종 평균 EPS, BPS, ROE
    /stock/{종목코드}/sector/daily : 종목 업종 평균 PER, PBR, PSR
    
    /stock/{종목코드}/years-price : 종목 5년치 주가
    /stock/{종목코드}/years-volume : 종목 5년치 거래량
    
    /stock/{종목코드}/statement : 종목 재무제표
    /stock/{종목코드}/statement/{type} : 종목 재무제표 항목별 디테일
    
    /stock/{종목코드}/evaluation : 종목 적정주가 (분기)
    /stock/{종목코드}/evaluation/daily : 종목 적정주가 (일일)
---
### 개발환경 및 사용 외부 라이브러리
#### 개발환경
    - Python 3.7.10
    - FASTapi 0.85.0
    - MySQL 8.0.31
#### 외부 라이브러리
    - Finance Data Reader : 시장지표 라이브러리
    - Marcap : 종목 주가데이터 라이브러리
