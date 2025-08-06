# PoliagentX/backend-poliagentx/data_preparation_expenditure.py

import pandas as pd
import numpy as np

def prepare_expenditure_data(exp_csv_path, indi_csv_path, output_exp_path, output_rel_path):
    data_exp = pd.read_csv(exp_csv_path)
    data_indi = pd.read_csv(indi_csv_path)

    data_exp = data_exp[data_exp.sdg.isin(data_indi.sdg.values)]
    data_exp = data_exp[data_exp.sdg.isin(data_indi[data_indi.instrumental==1].sdg.values)]

    years = [column_name for column_name in data_exp.columns if str(column_name).isnumeric()]
    periods = len(years)
    T = 69
    t = int(T/periods)

    new_rows = []
    for index, row in data_exp.iterrows():
        new_row = [row.sdg]
        for year in years:
            new_row += [int(row[year]) for i in range(t)]
        new_rows.append(new_row)
        
    df_exp = pd.DataFrame(new_rows, columns=['sdg']+list(range(T)))

    is_instrumental = dict(zip(data_indi.seriesCode, data_indi.instrumental==1))

    rel_dict = dict([(code, []) for code in data_indi.seriesCode if is_instrumental[code]])
    for index, row in data_indi.iterrows():
        if row.seriesCode in rel_dict:
            rel_dict[row.seriesCode].append(row.sdg)
        
    n_cols = max([len(value) for value in rel_dict.values()])

    M = [['' for i in range(n_cols+1)] for code in rel_dict.values()]
    for i, items in enumerate(rel_dict.items()):
        sdg, indis = items
        M[i][0] = sdg
        for j, indi in enumerate(indis):
            M[i][j+1] = indi

    df_rel = pd.DataFrame(M, columns=['seriesCode']+list(range(n_cols)))

    df_exp.to_csv(output_exp_path, index=False)
    df_rel.to_csv(output_rel_path, index=False)