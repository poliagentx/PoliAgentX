import pandas as pd

def expand_budget(data_exp):
    years = [col for col in data_exp.columns if str(col).isdigit()]
    periods = len(years)

    new_rows = []
    for _, row in data_exp.iterrows():
        new_row = [row.sdg]
        for year in years:
            # Keep as float, avoid truncating
            new_row.append(float(row[year]))
        new_rows.append(new_row)

    # Column names: 'sdg', then t0..tN
    return pd.DataFrame(new_rows, columns=['sdg'] + [f"t{j}" for j in range(periods)])
