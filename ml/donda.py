import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dbms import db
from sklearn.preprocessing import MinMaxScaler


conn = db.engine.connect()

# 삼성전자 머신러닝, 적정주가 계산
# 사용할 값 : 날짜, 시가, 종가, 저가, 고가, 거래량, per, pbr

# 1. Data Frame 가져오기
sql = "select date, code, close, open, high, low, volume, marcap, stocks, per, pbr, psr from stock_marcap where code = '005930' and per != 0"
data = conn.execute(sql).fetchall()
df = pd.DataFrame(data)

## 날짜 쪼개기
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.day

# 액면분할 => 값 수정
last_stock = df.iloc[-1]['stocks']
std = df['stocks'] / last_stock
df['close'] = round(df['close'] * std)
df['open'] = round(df['open'] * std)
df['high'] = round(df['high'] * std)
df['low'] = round(df['low'] * std)
df['volume'] = round(df['volume'] * (last_stock / df['stocks']))
df['per'] = round(df['per'] * std, 1)
df['pbr'] = round(df['pbr'] * std, 1)

print(df)

# 데이터 정규화 
scaler = MinMaxScaler()
scale_cols = ['close', 'open', 'high', 'low', 'volume', 'per', 'pbr']
df_scale = scaler.fit_transform(df[scale_cols])

df_scale = pd.DataFrame(df_scale)
df_scale.columns = scale_cols

print(df_scale)

# 데이터 셋
size = 200
train = df_scale[:-size]
test = df_scale[-size:]

def make_dataset(data, label, window_size):
    feature = []
    label = []

    for i in range(len(data) - window_size):
        feature.append(np.array(data.iloc[i:i+window_size]))
        label.append(np.array(label.iloc[i+window_size]))
    
    return np.array(feature), np.array(label)

f_cols = ['open', 'high', 'low', 'volume', 'per', 'pbr']
l_cols = ['close']

train_f = train[f_cols]
train_l = train[l_cols]
train_f, train_l = make_dataset(train_f, train_l, 20)
