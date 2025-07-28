import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

<<<<<<< HEAD
from PoliagentX.backend_poliagentx.policy_priority_inference import run_ppi,run_ppi_parallel
=======
from .policy_priority_inference import run_ppi  # Make sure this file is present in your project
>>>>>>> 26a294202ddf180ce84b253328241de9d403923c

def run_simulation(
    indicators_path,
    parameters_path,
    network_path,
    expenditure_path,
    relational_table_path,
    output_dir,
    T=30,
    sample_size=100
):
    # Load data
    df_indis = pd.read_csv(indicators_path)
    N = len(df_indis)
    I0 = df_indis.IF.values
    R = df_indis.instrumental
    qm = df_indis.qm.values
    rl = df_indis.rl.values
    indis_index = dict([(code, i) for i, code in enumerate(df_indis.indicator_label)])
    Imax = df_indis.maxVals.values
    Imin = df_indis.minVals.values

    df_params = pd.read_csv(parameters_path)
    alphas = df_params.alpha.values
    alphas_prime = df_params.alpha_prime.values
    betas = df_params.beta.values

    df_net = pd.read_csv(network_path)
    A = np.zeros((N, N))
    for index, row in df_net.iterrows():
        i = indis_index[row.origin]
        j = indis_index[row.destination]
        w = row.weight
        A[i, j] = w

    df_exp = pd.read_csv(expenditure_path)
    Bs_retrospective = df_exp.values[:, 1::]
    Bs = np.tile(Bs_retrospective[:, -1], (T, 1)).T

    df_rela = pd.read_csv(relational_table_path)
    B_dict = {}
    for index, row in df_rela.iterrows():
        B_dict[indis_index[row.indicator_label]] = [
            programme for programme in row.values[1::][row.values[1::].astype(str) != 'nan']
        ]

    goals = np.random.rand(N) * (Imax - I0) + I0

    outputs = []
    for sample in range(sample_size):
<<<<<<< HEAD
        output =run_ppi(
=======
        output = run_ppi(
>>>>>>> 26a294202ddf180ce84b253328241de9d403923c
            I0, alphas, alphas_prime, betas, A=A, R=R, qm=qm, rl=rl,
            Imax=Imax, Imin=Imin, Bs=Bs, B_dict=B_dict, T=T, G=goals
        )
        outputs.append(output)

    tsI, tsC, tsF, tsP, tsS, tsG = zip(*outputs)
    tsI_hat = np.mean(tsI, axis=0)

    new_rows = []
    for i, serie in enumerate(tsI_hat):
        new_row = [df_indis.iloc[i].indicator_label, df_indis.iloc[i].sdg, df_indis.iloc[i].color] + serie.tolist()
        new_rows.append(new_row)
    df_output = pd.DataFrame(new_rows, columns=['indicator_label', 'sdg', 'color'] + list(range(T)))
    df_output['goal'] = goals

    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, 'simulation_output.csv')
    df_output.to_csv(output_csv, index=False)

    # Optionally, save plots as images
    plt.figure(figsize=(8, 5))
    for index, row in df_output.iterrows():
        plt.plot(row[range(T)], color=row.color, linewidth=3)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    plt.xlim(0, T)
    plt.xlabel('time')
    plt.ylabel('indicator level')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'indicator_level.png'))
    plt.close()

    # ... (repeat for other plots as needed)

    return output_csv  # or return paths to generated files