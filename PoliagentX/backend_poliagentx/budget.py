import pandas as pd

def expand_budget(data_exp):
    years = [col for col in data_exp.columns if str(col).isdigit()]
    periods = len(years)
    T = 1 * periods
    t = int(T / periods)
    new_rows = []
    for _, row in data_exp.iterrows():
        new_row = [row.sdg]
        for year in years:
            new_row += [int(row[year]) for _ in range(t)]
        new_rows.append(new_row)
    return pd.DataFrame(new_rows, columns=['sdg'] + list(range(T)))

