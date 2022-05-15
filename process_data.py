from collections import defaultdict
from decimal import Decimal

#날짜별로 묶어주기
def dateisidx(datas):
    dict = defaultdict(list)    
    for data in datas:
        data = list(data)
        for i in range(1, len(data)):
            if type(data[i]) == Decimal:
                data[i] = float(data[i])

        dict[data[0]].append({"type": data[1], "close": data[2], "open": data[3],\
             "high": data[4], "low": data[5], "volume": data[6], "changes": data[7]})
    
    return dict

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

        date = data[0]
        code = data[1]
        name = data[2]
        close = data[4]
        changes = data[5]
        changes_ratio = data[6]
        open = data[7]
        high = data[8]
        low = data[9]
        volume = data[10]
        amount = data[11]
        marcap = data[12]
        stocks = data[13]
        per = data[14]
        pbr = data[15]
        #psr은 추가 예정

        dic[type].append({"date" : date, "code": code, "name" : name, "close" : close, "changes" : changes,
        "changes_ratio" : changes_ratio, "open" : open, "high" : high, "low" : low, "volume" : volume, "amount" : amount,
        "marcap" : marcap, "stocks" : stocks, "per" : per, "pbr" : pbr})
    
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
def data2grahp(datas):
    dict = defaultdict(list)
    for data in datas:
        data = list(data)
        dict[data[0]] = data[1]
    
    return dict

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
