import pandas as pd
import numpy as np

def build_relational_table(data_indi):
    is_instrumental = dict(zip(data_indi.indicator_label, data_indi.instrumental == 1))
    rel_dict = {code: [] for code in data_indi.indicator_label if is_instrumental[code]}
    for _, row in data_indi.iterrows():
        if row.indicator_label in rel_dict:
            rel_dict[row.indicator_label].append(row.sdg)
    n_cols = max(len(v) for v in rel_dict.values())
    M = [['' for _ in range(n_cols+1)] for _ in rel_dict.values()]
    for i, (sdg, indis) in enumerate(rel_dict.items()):
        M[i][0] = sdg
        for j, indi in enumerate(indis):
            M[i][j+1] = indi
    return pd.DataFrame(M, columns=['indicator_label'] + list(range(n_cols)))
