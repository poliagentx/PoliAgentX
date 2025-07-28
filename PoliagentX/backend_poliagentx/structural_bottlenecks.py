import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

<<<<<<< HEAD
from PoliagentX.backend_poliagentx.policy_priority_inference import run_ppi,run_ppi_parallel

=======
from .policy_priority_inference import run_ppi_parallel
>>>>>>> 26a294202ddf180ce84b253328241de9d403923c

def analyze_structural_bottlenecks(
    indicators_path,
    parameters_path,
    network_path,
    expenditure_path,
    relational_table_path,
    output_dir,
    T=30,
    parallel_processes=4,
    sample_size=1000
):
    """
    Analyze structural bottlenecks in policy implementation.
    
    Parameters:
    -----------
    indicators_path : str
        Path to the indicators CSV file
    parameters_path : str
        Path to the parameters CSV file
    network_path : str
        Path to the network CSV file
    expenditure_path : str
        Path to the expenditure CSV file
    relational_table_path : str
        Path to the relational table CSV file
    output_dir : str
        Directory to save output files and plots
    T : int
        Number of simulation periods
    parallel_processes : int
        Number of parallel processes for simulation
    sample_size : int
        Number of Monte Carlo simulations
    
    Returns:
    --------
    dict
        Dictionary containing analysis results and file paths
    """
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    df_indis = pd.read_csv(indicators_path)
    N = len(df_indis)
    I0 = df_indis.IF.values
    R = df_indis.instrumental
    qm = df_indis.qm.values
    rl = df_indis.rl.values
    indis_index = dict([(code, i) for i, code in enumerate(df_indis.seriesCode)])
    Imax = df_indis.maxVals.values
    Imin = df_indis.minVals.values
    goals = np.random.rand(N) * (Imax - I0) + I0

    # Load parameters
    df_params = pd.read_csv(parameters_path)
    alphas = df_params.alpha.values
    alphas_prime = df_params.alpha_prime.values
    betas = df_params.beta.values

    # Load network
    df_net = pd.read_csv(network_path)
    A = np.zeros((N, N))
    for index, row in df_net.iterrows():
        i = indis_index[row.origin]
        j = indis_index[row.destination]
        w = row.weight
        A[i, j] = w

    # Load expenditure data
    df_exp = pd.read_csv(expenditure_path)
    Bs_retrospective = df_exp.values[:, 1::]
    Bs = np.tile(Bs_retrospective[:, -1], (T, 1)).T

    # Load relational table
    df_rela = pd.read_csv(relational_table_path)
    B_dict = {}
    for index, row in df_rela.iterrows():
        B_dict[indis_index[row.indicator_label]] = [
            programme for programme in row.values[1::][row.values[1::].astype(str) != 'nan']
        ]

    # Run baseline simulation
    outputs_baseline = run_ppi_parallel(
        I0, alphas, alphas_prime, betas, A=A, R=R, qm=qm, rl=rl,
        Imax=Imax, Imin=Imin, Bs=Bs, B_dict=B_dict, T=T, G=goals,
        parallel_processes=parallel_processes, sample_size=sample_size
    )

    # Run frontier simulation
    frontier = np.ones(N)
    outputs_frontier = run_ppi_parallel(
        I0, alphas, alphas_prime, betas, A=A, R=R, qm=qm, rl=rl,
        Imax=Imax, Imin=Imin, Bs=Bs, B_dict=B_dict, T=T, G=goals, frontier=frontier,
        parallel_processes=parallel_processes, sample_size=sample_size
    )

    # Process results
    tsI_sample, tsC_sample, tsF_sample, tsP_sample, tsS_sample, tsG_sample = outputs_baseline
    tsI_baseline = np.mean(tsI_sample, axis=0)

    tsI_sample, tsC_sample, tsF_sample, tsP_sample, tsS_sample, tsG_sample = outputs_frontier
    tsI_frontier = np.mean(tsI_sample, axis=0)

    # Generate plots
    # Plot 1: Development gaps comparison
    plt.figure(figsize=(6, 6))
    for index, row in df_indis.iterrows():
        goal = goals[index]
        if goal > tsI_baseline[index, T-1]:
            plt.plot(goal - tsI_baseline[index, T-1], goal - tsI_frontier[index, T-1],
                     '.', mec='w', mfc=row.color, markersize=20)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    plt.xlabel('baseline development gap')
    plt.ylabel('development gap on the budgetary frontier')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'development_gaps_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # Plot 2: Gap reduction vs historical performance
    years = [c for c in df_indis.columns if str(c).isnumeric()]
    plt.figure(figsize=(12, 8))
    plt.fill_between([-.5, .5], [-.5, -.5], [.5, .5], color='grey', alpha=.25)
    
    for index, row in df_indis.iterrows():
        goal = goals[index]
        hist_performance = np.mean(row[years])
        if goal > tsI_baseline[index, T-1]:
            gap_base = goal - tsI_baseline[index, T-1]
            gap_frontier = np.max([0, goal - tsI_frontier[index, T-1]])
            gap_reduction = (gap_base - gap_frontier) / gap_base
            plt.plot(hist_performance, gap_reduction, '.', mec='w', mfc=row.color, markersize=40)
    
    for index, row in df_indis.iterrows():
        goal = goals[index]
        hist_performance = np.mean(row[years])
        if goal > tsI_baseline[index, T-1]:
            gap_base = goal - tsI_baseline[index, T-1]
            gap_frontier = np.max([0, goal - tsI_frontier[index, T-1]])
            gap_reduction = (gap_base - gap_frontier) / gap_base
            txt = plt.text(hist_performance, gap_reduction, row.indicator_label, color='black',
                           horizontalalignment='center')
            txt.set_bbox(dict(facecolor='white', alpha=0.25, edgecolor='white'))
    
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    plt.xlim(-.05, 1.05)
    plt.ylim(-.05, 1.05)
    plt.xlabel('historical performance')
    plt.ylabel('gap reduction')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'gap_reduction_analysis.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # Save analysis results
    results_data = []
    for index, row in df_indis.iterrows():
        goal = goals[index]
        hist_performance = np.mean(row[years])
        baseline_final = tsI_baseline[index, T-1]
        frontier_final = tsI_frontier[index, T-1]
        
        if goal > baseline_final:
            gap_base = goal - baseline_final
            gap_frontier = np.max([0, goal - frontier_final])
            gap_reduction = (gap_base - gap_frontier) / gap_base
        else:
            gap_base = 0
            gap_frontier = 0
            gap_reduction = 0
        
        results_data.append({
            'indicator_label': row.indicator_label,
            'sdg': row.sdg,
            'goal': goal,
            'baseline_final': baseline_final,
            'frontier_final': frontier_final,
            'gap_base': gap_base,
            'gap_frontier': gap_frontier,
            'gap_reduction': gap_reduction,
            'historical_performance': hist_performance,
            'is_bottleneck': goal > baseline_final
        })
    
    results_df = pd.DataFrame(results_data)
    results_path = os.path.join(output_dir, 'bottleneck_analysis_results.csv')
    results_df.to_csv(results_path, index=False)
    
    return {
        'results_csv': results_path,
        'development_gaps_plot': os.path.join(output_dir, 'development_gaps_comparison.png'),
        'gap_reduction_plot': os.path.join(output_dir, 'gap_reduction_analysis.png'),
        'bottleneck_count': len(results_df[results_df['is_bottleneck'] == True]),
        'total_indicators': N
    }