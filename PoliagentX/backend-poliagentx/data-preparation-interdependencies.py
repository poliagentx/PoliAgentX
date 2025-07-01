import pandas as pd
import numpy as np

data = pd.read_csv('https://raw.githubusercontent.com/oguerrer/ppi/main/tutorials/clean_data/data_indicators.csv')


N = len(data)
M = np.zeros((N, N))
years = [column_name for column_name in data.columns if str(column_name).isnumeric()]

for i, rowi in data.iterrows():
    for j, rowj in data.iterrows():
        if i!=j:
            serie1 = rowi[years].values.astype(float)[1::]
            serie2 = rowj[years].values.astype(float)[0:-1]
            change_serie1 = serie1[1::] - serie1[0:-1]
            change_serie2 = serie2[1::] - serie2[0:-1]
            if not np.all(change_serie1 == change_serie1[0]) and not np.all(change_serie2 == change_serie2[0]):
                M[i,j] = np.corrcoef(change_serie1, change_serie2)[0,1]

M[np.abs(M) < 0.5] = 0
ids = data.seriesCode.values
edge_list = []
for i, j in zip(np.where(M!=0)[0], np.where(M!=0)[1]):
    edge_list.append( [ids[i], ids[j], M[i,j]] )
df = pd.DataFrame(edge_list, columns=['origin', 'destination', 'weight'])
df.to_csv('clean_data/data_network.csv', index=False)