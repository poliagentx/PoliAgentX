import pandas as pd
import numpy as np
import policy_priority_inference as ppi

def calibrate_model(indicators_path,relational_table_path, network_path,expenditure_path,output_path,threshold=0.7,parallel_processes=4,low_precision_counts=50):
    df_indis = pd.read_excel(indicators_path)
    N = len(df_indis)
    I0 = df_indis.I0.values
    IF = df_indis.IF.values
    success_rates = df_indis.successRates.values
    R = df_indis.instrumental
    qm = df_indis.qm.values
    rl = df_indis.rl.values
    indis_index = dict([(code, i) for i, code in enumerate(df_indis.indicator_label)])

    df_net = pd.read_excel(network_path)
    A = np.zeros((N, N))
    for index, row in df_net.iterrows():
        i = indis_index[row.origin]
        j = indis_index[row.destination]
        w = row.weight
        A[i, j] = w

    df_exp = pd.read_excel(expenditure_path)
    Bs = df_exp.values[:, 1::]
    df_rela = pd.read_excel(relational_table_path)
    B_dict = {}
    for index, row in df_rela.iterrows():
        B_dict[indis_index[row.indicator_label]] = [programme for programme in row.values[1::][row.values[1::].astype(str) != 'nan']]

    T = Bs.shape[1]

    parameters = ppi.calibrate(
        I0, IF, success_rates, A=A, R=R, qm=qm, rl=rl, Bs=Bs, B_dict=B_dict,
        T=T, threshold=threshold, parallel_processes=parallel_processes, verbose=True,
        low_precision_counts=low_precision_counts
    )
    df_params = pd.DataFrame(parameters[1::], columns=parameters[0])
    df_params.to_excel(output_path, index=False)
    return output_path