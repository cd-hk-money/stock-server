import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dbms import db
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import Dense
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.layers import LSTM

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

# 데이터 정규화 
scaler = MinMaxScaler()
scale_cols = ['close', 'open', 'high', 'low', 'volume', 'per', 'pbr']
df_scale = scaler.fit_transform(df[scale_cols])

df_scale = pd.DataFrame(df_scale)
df_scale.columns = scale_cols

# 데이터 셋
size = 200
train = df_scale[:-size]
test = df_scale[-size:]

def make_dataset(data, label, window_size):
    f_list= []
    l_list = []

    for i in range(len(data) - window_size):
        f_list.append(np.array(data.iloc[i:i+window_size]))
        l_list.append(np.array(label.iloc[i+window_size]))
    
    return np.array(f_list), np.array(l_list)

f_cols = ['open', 'high', 'low', 'volume', 'per', 'pbr']
l_cols = ['close']

train_f = train[f_cols]
train_l = train[l_cols]

train_f, train_l = make_dataset(train_f, train_l, 20)
x_train, x_valid, y_train, y_valid = train_test_split(train_f, train_l, test_size=0.2)

test_f = test[f_cols]
test_l = test[l_cols]

test_f, test_l = make_dataset(test_f, test_l, 20)

# 모형 학습
model = Sequential()
model.add(LSTM(16,
                input_shape=(train_f.shape[1], train_f.shape[2]),
                activation='relu',
                return_sequences=False)
            )

model.add(Dense(1))

model.compile(loss='mean_squared_error', optimizer='adam')
early_stop = EarlyStopping(monitor='val_loss', patience=40)

model_path = 'model'
filename = os.path.join(model_path, 'tmp_checkpoint.h5')
checkpoint = ModelCheckpoint(filename, monitor='val_loss', verbose=1, save_best_only=True, mode='auto')

history = model.fit(x_train, y_train,
                                    epochs=200,
                                    batch_size=16,
                                    validation_data=(x_valid, y_valid),
                                    callbacks=[early_stop, checkpoint])
                                
model.load_weights(filename)
pred = model.predict(test_f)

plt.figure(figsize=(12, 9))
plt.plot(test_l, label = 'actual')
plt.plot(pred, label = 'prediction')
plt.legend()
plt.show()
