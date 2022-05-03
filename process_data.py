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
