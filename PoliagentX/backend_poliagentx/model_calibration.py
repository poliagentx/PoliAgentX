# import pandas as pd
# import numpy as np
# # import policy_priority_inference as ppi
# from PoliagentX.backend_poliagentx.policy_priority_inference import calibrate
# with open('indicator_path.txt', 'r') as f:
#     path_indicator = f.read().strip()

# with open('network_path.txt', 'r') as f:
#     path_network = f.read().strip()

# with open('generated_budget_path.txt', 'r') as f:
#     path_generated_budget = f.read().strip()


# #indicators before calibration
# df_indis = pd.read_excel(path_indicator,sheet_name='template')
# N = len(df_indis) # number of indicators
# I0 = df_indis.initial_value.values # initial values
# IF = df_indis.final_value.values # final values
# success_rates = df_indis.success_rate.values # success rates
# R = df_indis.instrumental # instrumental indicators
# qm = df_indis.monitoring.values # quality of monitoring
# rl = df_indis.rule_of_law.values # quality of the rule of law
# indis_index = dict([(code, i) for i, code in enumerate(df_indis.indicator_label)]) 

# # network matrix
# df_net = pd.read_excel( path_network,sheet_name='template_network')
# A = df_net.values[:,1::]

# # Bs disbursement schedule
# df_exp = pd.read_excel(path_generated_budget,sheet_name='template_budget')
# Bs = df_exp.values[:,1::] # disbursement schedule (assumes that the expenditure programmes are properly sorted)



# #budget indicator mapping
# df_rela = df_rela = pd.read_excel(path_generated_budget, sheet_name='template_relation_table')
# B_dict = {} # PPI needs the relational table in the form of a Python dictionary
# for index, row in df_rela.iterrows():
#  B_dict[indis_index[row.indicator_label]] = [programme for programme in row.values[1::][row.values[1::].astype(str)!='nan']]
 
 
#  T = Bs.shape[1]
# parallel_processes = 4 # number of cores to use
# threshold = 0.7 # the quality of the calibration (I choose a medium quality for illustration purposes)
# low_precision_counts = 50 # number of low-quality iterations to accelerate the calibration

# parameters = calibrate(I0, IF, success_rates, A=A, R=R, qm=qm, rl=rl, Bs=Bs, B_dict=B_dict,
#               T=T, threshold=threshold, parallel_processes=parallel_processes, verbose=True,
#              low_precision_counts=low_precision_counts)