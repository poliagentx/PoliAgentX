import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import requests
url = 'https://raw.githubusercontent.com/oguerrer/ppi/main/source_code/policy_priority_inference.py'
r = requests.get(url)
with open('policy_priority_inference.py', 'w') as f:
    f.write(r.text)
import policy_priority_inference as ppi

# INDICATORS
df_indis = pd.read_csv('./clean_data/data_indicators.csv')
N = len(df_indis) # number of indicators
I0 = df_indis.IF.values # initial values
R = df_indis.instrumental # instrumental indicators
qm = df_indis.qm.values # quality of monitoring
rl = df_indis.rl.values # quality of the rule of law
indis_index = dict([(code, i) for i, code in enumerate(df_indis.seriesCode)]) # used to build the network matrix
Imax = df_indis.maxVals.values
Imin = df_indis.minVals.values
goals = np.random.rand(N)*(Imax - I0) + I0

# PARAMETERS
df_params = pd.read_csv('./clean_data/parameters.csv')
alphas = df_params.alpha.values
alphas_prime = df_params.alpha_prime.values
betas = df_params.beta.values

# NETWORK
df_net = pd.read_csv('./clean_data/data_network.csv')
A = np.zeros((N, N)) # adjacency matrix
for index, row in df_net.iterrows():
    i = indis_index[row.origin]
    j = indis_index[row.destination]
    w = row.weight
    A[i,j] = w

# DISBURSEMENT SCHEDULE (make sure that the disbursement schedule is consistent with T, otherwise PPI will simulate the T of the calibration)
T = 30
df_exp = pd.read_csv('./clean_data/data_expenditure.csv')
Bs_retrospective = df_exp.values[:,1::] # disbursement schedule (assumes that the expenditure programmes are properly sorted)
# Create a new disbursement schedule assuming that expenditure will be the same as the last period of the sample
Bs = np.tile(Bs_retrospective[:,-1], (T,1)).T

# RELATIONAL TABLE
df_rela = pd.read_csv('./clean_data/data_relational_table.csv')
B_dict = {}
for index, row in df_rela.iterrows():
    B_dict[indis_index[row.seriesCode]] = [programme for programme in row.values[1::][row.values[1::].astype(str)!='nan']]

parallel_processes=4
sample_size=1000 # now we increase the sample size from 100 (which was used in the previous tutorial) to 1000

# first the baseline
outputs_baseline = ppi.run_ppi_parallel(I0, alphas, alphas_prime, betas, A=A, R=R, qm=qm, rl=rl,
                                        Imax=Imax, Imin=Imin, Bs=Bs, B_dict=B_dict, T=T, G=goals,
                                        parallel_processes=parallel_processes, sample_size=sample_size)

# now the frontier
# notice that Bs and B_dict will be overridden by frontier
frontier = np.ones(N)
outputs_frontier = ppi.run_ppi_parallel(I0, alphas, alphas_prime, betas, A=A, R=R, qm=qm, rl=rl,
                                        Imax=Imax, Imin=Imin, Bs=Bs, B_dict=B_dict, T=T, G=goals, frontier=frontier,
                                        parallel_processes=parallel_processes, sample_size=sample_size)

tsI_sample, tsC_sample, tsF_sample, tsP_sample, tsS_sample, tsG_sample = outputs_baseline
tsI_baseline = np.mean(tsI_sample, axis=0)

tsI_sample, tsC_sample, tsF_sample, tsP_sample, tsS_sample, tsG_sample = outputs_frontier
tsI_frontier = np.mean(tsI_sample, axis=0)

plt.figure(figsize=(6, 6))
for index, row in df_indis.iterrows():
    goal = goals[index]
    if goal > tsI_baseline[index,T-1]: # consider only those indicators that would not reach their goals
        plt.plot(goal-tsI_baseline[index,T-1], goal-tsI_frontier[index,T-1],
                 '.', mec='w', mfc=row.color, markersize=20)
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)
plt.xlabel('baseline development gap')
plt.ylabel('development gap on the budgetary frontier')
plt.tight_layout()

years = [c for c in df_indis.columns if str(c).isnumeric()]
plt.figure(figsize=(12, 8))
plt.fill_between([-.5, .5], [-.5, -.5], [.5, .5], color='grey', alpha=.25)
for index, row in df_indis.iterrows():    
    goal = goals[index]
    hist_performance = np.mean(row[years])
    if goal > tsI_baseline[index,T-1]:
        gap_base = goal-tsI_baseline[index,T-1]
        gap_frontier = np.max([0, goal-tsI_frontier[index,T-1]])
        gap_reduction = (gap_base - gap_frontier)/gap_base
        plt.plot(hist_performance, gap_reduction, '.', mec='w', mfc=row.color, markersize=40)
for index, row in df_indis.iterrows():    
    goal = goals[index]
    hist_performance = np.mean(row[years])
    if goal > tsI_baseline[index,T-1]:
        gap_base = goal-tsI_baseline[index,T-1]
        gap_frontier = np.max([0, goal-tsI_frontier[index,T-1]])
        gap_reduction = (gap_base - gap_frontier)/gap_base
        txt = plt.text(hist_performance, gap_reduction, row.seriesCode, color='black', 
                       horizontalalignment='center')
        txt.set_bbox(dict(facecolor='white', alpha=0.25, edgecolor='white'))
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)
plt.xlim(-.05, 1.05)
plt.ylim(-.05, 1.05)
plt.xlabel('historical performance')
plt.ylabel('gap reduction')
plt.tight_layout()
