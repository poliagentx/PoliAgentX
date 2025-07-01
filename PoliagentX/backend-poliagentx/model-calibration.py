import pandas as pd
import numpy as np

import requests # the Python library that helps placing requests to websites
url = 'https://raw.githubusercontent.com/oguerrer/ppi/main/source_code/policy_priority_inference.py'
r = requests.get(url)
with open('policy_priority_inference.py', 'w') as f:
    f.write(r.text)
import policy_priority_inference as ppi

df_indis = pd.read_csv('./clean_data/data_indicators.csv')

N = len(df_indis) # number of indicators(rows)
I0 = df_indis.I0.values # initial values
IF = df_indis.IF.values # final values
success_rates = df_indis.successRates.values # success rates
R = df_indis.instrumental # instrumental indicators
qm = df_indis.qm.values # quality of monitoring
rl = df_indis.rl.values # quality of the rule of law
indis_index = dict([(code, i) for i, code in enumerate(df_indis.seriesCode)]) # used to build the network matrix

df_net = pd.read_csv('./clean_data/data_network.csv')

A = np.zeros((N, N)) # adjacency matrix
for index, row in df_net.iterrows():
    i = indis_index[row.origin]
    j = indis_index[row.destination]
    w = row.weight
    A[i,j] = w

df_exp = pd.read_csv('./clean_data/data_expenditure.csv')

Bs = df_exp.values[:,1::] # disbursement schedule (assumes that the expenditure programmes are properly sorted)
df_rela = pd.read_csv('./clean_data/data_relational_table.csv')

B_dict = {} # PPI needs the relational table in the form of a Python dictionary
for index, row in df_rela.iterrows():
    B_dict[indis_index[row.seriesCode]] = [programme for programme in row.values[1::][row.values[1::].astype(str)!='nan']]

T = Bs.shape[1]
parallel_processes = 4 # number of cores to use
threshold = 0.6 # the quality of the calibration (I choose a medium quality for illustration purposes)
low_precision_counts = 50 # number of low-quality iterations to accelerate the calibration

parameters = ppi.calibrate(I0, IF, success_rates, A=A, R=R, qm=qm, rl=rl, Bs=Bs, B_dict=B_dict,
              T=T, threshold=threshold, parallel_processes=parallel_processes, verbose=True,
             low_precision_counts=low_precision_counts)
df_params = pd.DataFrame(parameters[1::], columns=parameters[0])
df_params.to_csv('clean_data/parameters.csv', index=False)