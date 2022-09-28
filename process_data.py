from collections import defaultdict
from decimal import Decimal

#날짜별로 묶어주기
def dateisidx(datas):
    dic = defaultdict(list)
        
    for data in datas:
        data = list(data)
        for i in range(1, len(data)):
            if type(data[i]) == Decimal:
                data[i] = float(data[i])

        temp = {data[1]: dict()}
        temp[data[1]] = {"close": data[2], "open": data[3], "high": data[4], "low": data[5], "volume": data[6], "changes": data[7]}

        dic[data[0]].append(temp)
        
    return dic     
        
#기업 : 코드 매칭
def codelist(datas):
    dict = defaultdict(list)
    for data in datas:
        data = list(data)
        dict[data[0]] = data[1]
    
    return dict

#오늘의 TOP 10
def findtop(type, datas):
    dic = {type: []}
    for data in datas:
        data = list(data)
        dic[type].append(data)
    
    return dic

#랜덤 추천종목 key, value 매칭
def matchrecom(datas):
    dic = dict()
    for data in datas:
        data = list(data)

        if data[0] in dic:
            dic[data[0]].append({"name": data[1], "close": data[2], "changes_ratio": data[3]})
        else:
            dic[data[0]] = {"name": data[1], "close": data[2], "changes_ratio": data[3]}
    return dic

#그래프 위해 날짜 꺼내주기
def data2graph(datas):
    dic = {"origin": dict()}

    for data in datas:
        data = list(data)
        dic["origin"][data[0]] = data[1]
        
    return dic

#종가 그래프용
def data2graph2(datas):
    dic = {"close" : dict()}
    
    dates = []
    value = []
    for data in datas:
        data = list(data)

        dates.append(data[0])
        value.append(data[1])

    dic["close"]["date"] = dates
    dic["close"]["values"] = value
    
    return dic

#ebitda, revenue 그래프용
def data2graph3(datas, type):
    dic = {type: dict()}

    dates = []
    value = []
    for data in datas:
        data = list(data)

        dates.append(data[0])
        value.append(data[1])

    dic[type]["date"] = dates
    dic[type]["values"] = value
    
    return dic
#재무제표 key, value 맞춰주기
def state2dict(datas):
    dict = defaultdict(list)
    for data in datas:
        data = list(data)
        
        dict[data[1]].append({"type": data[2], "asset": data[3], "equity": data[4], "equity_non": data[5], "liability": data[6],\
            "current_asset": data[7], "profit": data[8], "profit_non": data[9], "revenue": data[10], "cash": data[11], "ebitda": data[13], \
                "gross_margin": data[14]})

    return dict

#보조지표 key, value 맞춰주기
def indi2dict(datas):
    dict = defaultdict(list)
    for data in datas:
        data = list(data)

        dict[data[1]].append({"type": data[2], "eps": data[3], "bps": data[4], "roe": data[5]})
    
    return dict

# 업종평균 key, value 맞춰주기
def sector2dict(datas):
    dict = defaultdict(list)
    for data in datas:
        data = list(data)

        dict[data[0]].append({"per": data[1], "pbr": data[2], "psr": data[3]})
    return dict

# 업종평균 EPS, BPS, ROE key, value 맞추기
def sectorqu2dict(datas):
    dict = defaultdict(list)
    for date, eps, bps, roe in datas:
        dict["date"].append(date)
        dict["sector_eps"].append(eps)
        dict["sector_bps"].append(bps)
        dict["sector_roe"].append(roe)

    return dict

# 적정주가 key, value 맞춰주기
def evulation2json(datas):
    dic = defaultdict(list)

    for date, v1, v2 in datas:
        dic["date"].append(date)
        dic["proper-price"].append(v1)
        dic["S-rim"].append(v2)
        
    return dic

def daily_evalu(datas):
    dic = defaultdict(list)

    for date, v in datas:
        dic["date"].append(date)
        dic["value"].append(v)
    
    return dic

# 기업의 1년 per, pbr, psr
def daily_indicator(datas):
    dic = defaultdict(list)

    for date, per, pbr, psr in datas:
        dic[date].append({"PER": per, "PBR": pbr, "PSR": psr})
    
    return dic

# # 유사종목 key, value 맞춰주기
def similarStock(datas):
    dic = []
    
    for code, name, market, close, changes, changes_ratio in datas:
        dic.append({"code":code, "Nmae": name, "Market": market, "close": close, "changes": changes, "changes_ratio":changes_ratio})
        
    return dic