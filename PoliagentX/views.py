import tempfile
from io import BytesIO
import uuid
import os
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from PoliagentX.backend_poliagentx.policy_priority_inference import calibrate
from PoliagentX.backend_poliagentx.policy_priority_inference import run_ppi,run_ppi_parallel
from PoliagentX.backend_poliagentx.parameters import save_parameters_to_excel
from PoliagentX.backend_poliagentx.relational_table import build_relational_table
from PoliagentX.backend_poliagentx.allocation import get_sdg_allocation_from_file,SDG_ALLOCATION
from PoliagentX.backend_poliagentx.budget import expand_budget
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from openpyxl import Workbook
from .forms import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.staticfiles import finders
import pandas as pd
import numpy as np
import tempfile
from openpyxl.utils.dataframe import dataframe_to_rows
import matplotlib.pyplot as plt


def upload_indicators(request):
    if request.method == 'POST':
        form = Uploaded_indicators(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['government_indicators']

            # Save file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                temp_file_path = tmp.name

            # Load Excel data
            try: 
                data = pd.read_excel(temp_file_path)
                data_filtered = data.drop(['monitoring', 'rule_of_law'], axis=1)
            except Exception as e:
                messages.error(request, f"❌ Failed to read Excel file: {str(e)}")
                return render(request, 'indicators.html', {'form': form})

            # Identify year columns
            years = [col for col in data_filtered.columns if str(col).isdigit()]
            
            # Normalize and invert indicators
            normalised_series = []
            for index, row in data_filtered.iterrows():
                try:
                    time_series = row[years].values.astype(float)
                    norm = (time_series - row['worstBound']) / (row['bestBound'] - row['worstBound'])
                    if row['invert'] == 1:
                        norm = 1 - norm
                    normalised_series.append(norm)
                except Exception as e:
                    messages.error(request, f"❌ Error processing row {index}: {str(e)}")
                    return render(request, 'indicators.html', {'form': form})

            # Create DataFrame with normalized values
            df = pd.DataFrame(normalised_series, columns=years)
            df['indicator_label'] = data['indicator_label']
            df['sdg'] = data['sdg']
            df['min_value'] = 0
            df['max_value'] = 1
            df['instrumental'] = data['instrumental']
            df['indicator_name'] = data['indicator_name']
            df['color'] = data['color']

            # Add I0, IF
            df['I0'] = df[years[0]]
            df['IF'] = df[years[-1]]

            # Success Rates
            diff = df[years].diff(axis=1).iloc[:, 1:]
            success_rates = (diff > 0).sum(axis=1) / (len(years) - 1)
            success_rates = success_rates.clip(lower=0.05, upper=0.95)
            df['success_rates'] = success_rates

            # Assure development gaps
            df.loc[df['I0'] == df['IF'], 'IF'] *= 1.05

            # Governance parameters
            df['qm'] = data['monitoring']
            df['rl'] = data['rule_of_law']
            

            # Save to cleaned Excel
            # os.makedirs('clean_data', exist_ok=True)
            # output_path = os.path.join('clean_data', 'data_indicators.xlsx')
            # df.to_excel(output_path, index=False)

            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            tmp_file.close()  # close it so ExcelWriter can open it by name

            with pd.ExcelWriter(tmp_file.name) as writer:
                df.to_excel(writer, sheet_name='template', index=False)

            request.session['indicators_path'] = tmp_file.name


            messages.success(request, "☑️ File uploaded and processed successfully.")
            return render(request, 'indicators.html', {'form': Uploaded_indicators()})

        return render(request, 'indicators.html', {'form': form})

    return render(request, 'indicators.html', {'form': Uploaded_indicators()})

def budgets_page(request):
    indicators_path = request.session.get('indicators_path')
    if not indicators_path:
        messages.error(request, "Indicators file is missing. Please upload it first.")
        return redirect('upload_indicators')

    allocation = get_sdg_allocation_from_file(indicators_path)
    budget_form = BudgetForm()
    upload_form = Uploaded_Budget()
    data_exp = None

    if request.method == 'POST':
        data_indi = pd.read_excel(indicators_path)

        # Handle uploaded Excel file
        if 'government_expenditure' in request.FILES:
            upload_form = Uploaded_Budget(request.POST, request.FILES)
            if not upload_form.is_valid():
                messages.error(request, "❌ Invalid file upload.")
                return redirect('budgets_page')

            try:
                uploaded_file = request.FILES['government_expenditure']
                data_exp = pd.read_excel(BytesIO(uploaded_file.read()))

                if 'sdg' not in data_exp.columns:
                    messages.error(request, "❌ Uploaded file must have an 'sdg' column.")
                    return redirect('budgets_page')

                # Filter for matching & instrumental SDGs
                data_exp = data_exp[data_exp.sdg.isin(data_indi.sdg.values)]
                data_exp = data_exp[data_exp.sdg.isin(data_indi[data_indi.instrumental == 1].sdg.values)]

            except Exception as e:
                messages.error(request, f"❌ Failed to read uploaded file: {e}")
                return redirect('budgets_page')

        # Handle manual budget input
        elif 'budget' in request.POST:
            budget_form = BudgetForm(request.POST)
            if not budget_form.is_valid():
                messages.error(request, "❌ Invalid manual budget input.")
                return redirect('budgets_page')

            budget = budget_form.cleaned_data['budget']
            inflation = budget_form.cleaned_data['inflation_rate']
            adjusted_budget = budget / (1 + (inflation / 100))

            years = sorted([int(col) for col in data_indi.columns if str(col).isdigit()])
            periods = len(years)

            data_exp = pd.DataFrame([
                {
                    'sdg': i + 1,
                    **{str(years[0] + j): round(adjusted_budget * sdg['percent'] / 100 / periods, 2) for j in range(periods)}
                }
                for i, sdg in enumerate(allocation)
            ])

            if 'sdg' not in data_exp.columns:
                messages.error(request, "❌ Data is missing an 'sdg' column.")
                return redirect('budgets_page')

            data_exp = data_exp[data_exp.sdg.isin(data_indi.sdg.values)]
            data_exp = data_exp[data_exp.sdg.isin(data_indi[data_indi.instrumental == 1].sdg.values)]

        else:
            # No relevant POST data, just render the form
            return render(request, 'budgets.html', {'budget_form': budget_form, 'upload_form': upload_form})

        # Expand budget and build relational table
        df_exp = expand_budget(data_exp)
        df_rel = build_relational_table(data_indi)

        # Save results to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            with pd.ExcelWriter(tmp_file.name) as writer:
                df_exp.to_excel(writer, sheet_name='template_budget', index=False)
                df_rel.to_excel(writer, sheet_name='relational_table', index=False)

            request.session['budget_file_path'] = tmp_file.name

        return redirect('upload_network')

    return render(request, 'budgets.html', {
        'budget_form': budget_form,
        'upload_form': upload_form,
    })



def upload_network(request):
    indicators_path = request.session.get('indicators_path')
    if not indicators_path:
        messages.error(request, "Indicators file is missing. Please upload it first.")
        return redirect('upload_indicators')

    skip_form = Skip_networks()
    uploaded_form = Uploaded_networks()
    data_net = None

    if request.method == 'POST':
        # User uploaded a file
        if 'interdependency_network' in request.FILES:
            uploaded_form = Uploaded_networks(request.POST, request.FILES)
            if uploaded_form.is_valid():
                uploaded_file = request.FILES['interdependency_network']
                try:
                    data_net = pd.read_excel(BytesIO(uploaded_file.read()))
                except Exception as e:
                    messages.error(request, f"❌ Failed to read uploaded file: {e}")
                    return redirect('upload_network')

        # User chose to skip network upload, generate default network
        elif 'skip-network' in request.POST:
            skip_form = Skip_networks(request.POST)
            if skip_form.is_valid():
                data_indi = pd.read_excel(indicators_path)
                years = sorted([col for col in data_indi.columns if str(col).strip().isdigit()])
                data_array = data_indi[years].astype(float).values

                change_serie1_all = data_array[:, 2:] - data_array[:, 1:-1]
                change_serie2_all = data_array[:, 1:-1] - data_array[:, :-2]

                def is_not_constant(arr):
                    return np.any(arr != arr[0])

                valid_c1 = np.array([is_not_constant(row) for row in change_serie1_all])
                valid_c2 = np.array([is_not_constant(row) for row in change_serie2_all])

                N = len(data_indi)
                M = np.zeros((N, N))

                valid_i = np.where(valid_c1)[0]
                valid_j = np.where(valid_c2)[0]

                for i in valid_i:
                    c1 = change_serie1_all[i]
                    for j in valid_j:
                        if i != j:
                            c2 = change_serie2_all[j]
                            M[i, j] = np.corrcoef(c1, c2)[0, 1]

                M[np.abs(M) < 0.5] = 0

                ids = data_indi.indicator_label.values
                edge_list = [[ids[i], ids[j], M[i, j]] for i, j in zip(*np.where(M != 0))]
                data_net = pd.DataFrame(edge_list, columns=['origin', 'destination', 'weight'])
     
        else:
            # No relevant POST data, just render the form
            return render(request, 'Network.html', {'skip_form': skip_form, 'uploaded_form': uploaded_form})
        
        # Save the network dataframe to Excel files and session path
        if data_net is not None:
            wb = Workbook()
            ws_network = wb.active
            ws_network.title = "template_network"
            for r in dataframe_to_rows(data_net, index=False, header=True):
                ws_network.append(r)

            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                wb.save(tmp_file.name)
                # tmp_file.close() # context manager closes automatically
                request.session['network_path'] = tmp_file.name

          
        return redirect('calibration')

    return render(request, 'Network.html', {
        'skip_form': skip_form,
        'uploaded_form': uploaded_form,
    })

       
def simulation(request):
    return render(request,'simulation.html')
def calibration(request):
    return render(request,'calibration.html')



def download_indicator_template(request):
    filepath = finders.find('templates/template_indicators.xlsx')
    if filepath and os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='template_indicators.xlsx')
    else:
        return HttpResponse("Template file not found.", status=404)

def download_budget_template(request):
    filepath = finders.find('templates/template_budget.xlsx')
    if filepath and os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='template_budget.xlsx')
    else:
        return HttpResponse("Template file not found.", status=404)

def download_network_template(request):
    filepath = finders.find('templates/template_network.xlsx')
    if filepath and os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='template_network.xlsx')
    else:
        return HttpResponse("Template file not found.", status=404)


def run_calibration(request, threshold=0.7):
    indicators_path = request.session.get('indicators_path')
    network_path = request.session.get('network_path')
    budget_path = request.session.get('budget_file_path')
   
    # --- Load indicator data ---
    df_indis = pd.read_excel(indicators_path)
    N = len(df_indis)
    I0 = df_indis.I0.values
    IF = df_indis.IF.values
    success_rates = df_indis.success_rates.values
    R = df_indis.instrumental
    qm = df_indis.qm.values
    rl = df_indis.rl.values
    indis_index = dict([(code, i) for i, code in enumerate(df_indis.indicator_label)])

    # --- Load network ---
    df_net = pd.read_excel(network_path)
    A = np.zeros((N, N))
    for index, row in df_net.iterrows():
        i = indis_index[row.origin]
        j = indis_index[row.destination]
        A[i, j] = row.weight

    # --- Load budget matrix ---
    df_exp = pd.read_excel(budget_path, sheet_name='template_budget')
    Bs = df_exp.values[:, 1:]

    # --- Load relational table ---
    df_rela = pd.read_excel(budget_path, sheet_name='relational_table')
    B_dict = {}
    for index, row in df_rela.iterrows():
        B_dict[indis_index[row.indicator_label]] = [
            programme for programme in row.values[1:] if str(programme) != 'nan'
        ]

    T = Bs.shape[1]
    parallel_processes = 4
    low_precision_counts = 50

    # --- Run calibration ---
    parameters = calibrate(
        I0, IF, success_rates, A=A, R=R, qm=qm, rl=rl, Bs=Bs, B_dict=B_dict,
        T=T, threshold=threshold, parallel_processes=parallel_processes,
        verbose=True, low_precision_counts=low_precision_counts
    )

    return parameters

@csrf_exempt
def start_calibration(request):
    if request.method == 'POST':
        try:
            threshold = float(request.POST.get('threshold', 0.7))
        except (ValueError, TypeError):
            threshold = 0.7

        parameters = run_calibration(request, threshold=threshold)
        parameters = pd.DataFrame(parameters)

        

        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "parameters"
        for row in dataframe_to_rows(parameters, index=False, header=True):
            ws.append(row)

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_path = tmp_file.name
        wb.save(tmp_path)

        # Store in session
        request.session['param_excel_path'] = tmp_path

        return render(request, 'calibration.html', {
            'threshold': threshold,
            'parameters': parameters.to_numpy().tolist()  # so you can render easily
        })


def run_simulation(request):
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('simulation')

    # Retrieve paths from session
    param_excel_path = request.session.get('param_excel_path')
    network_path = request.session.get('network_path')
    budget_path = request.session.get('budget_file_path')
    indicators_path = request.session.get('indicators_path')

    if not all([param_excel_path, network_path, budget_path, indicators_path]):
        messages.error(request, "Missing required files for simulation.")
        return redirect('calibration')

    try:
        # Load indicators
        df_indis = pd.read_excel(indicators_path)
        N = len(df_indis)
        I0 = df_indis.I0.values
        R = df_indis.instrumental
        qm = df_indis.qm.values
        rl = df_indis.rl.values
        indis_index = {code: i for i, code in enumerate(df_indis.indicator_label)}
        Imax = df_indis.max_value.values
        Imin = df_indis.min_value.values

        # Load parameters
        df_params = pd.read_excel(param_excel_path, skiprows=1)
        alpha = df_params.alpha.values
        alpha_prime = df_params.alpha_prime.values
        betas = df_params.beta.values

        # Load network matrix
        df_net = pd.read_excel(network_path)
        A = np.zeros((N, N))
        for _, row in df_net.iterrows():
            i = indis_index[row.origin]
            j = indis_index[row.destination]
            A[i, j] = row.weight

        # Number of simulations
        T = int(request.POST.get("num_simulations", 50))

        # Load budget
        df_exp = pd.read_excel(budget_path, sheet_name='template_budget')
        Bs_retrospective = df_exp.values[:, 1:]
        Bs = np.tile(Bs_retrospective[:, -1], (T, 1)).T

        # Load relational table
        df_rela = pd.read_excel(budget_path, sheet_name='relational_table')
        B_dict = {
            indis_index[row.indicator_label]: [
                prog for prog in row.values[1:] if pd.notna(prog)
            ]
            for _, row in df_rela.iterrows()
        }

        # Generate random goals
        goals = np.random.rand(N) * (Imax - I0) + I0

        # Run simulations
        sample_size = 100
        outputs = []
        for _ in range(sample_size):
            output = run_ppi(
                I0, alpha, alpha_prime, betas,
                A=A, Bs=Bs, B_dict=B_dict, T=T, R=R, qm=qm, rl=rl,
                Imax=Imax, Imin=Imin, G=goals
            )
            outputs.append(output)

        tsI, tsC, tsF, tsP, tsS, tsG = zip(*outputs)
        tsI_hat = np.mean(tsI, axis=0)

        # Prepare output DataFrame
        new_rows = [
            [df_indis.iloc[i].indicator_label, df_indis.iloc[i].sdg, df_indis.iloc[i].color] + serie.tolist()
            for i, serie in enumerate(tsI_hat)
        ]
        df_output = pd.DataFrame(new_rows, columns=['indicator_label', 'sdg', 'color'] + list(range(T)))
        df_output['goal'] = goals

        # Ensure media folder exists
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        plot_urls = []

        def save_plot(fig):
            filename = f"plot_{uuid.uuid4().hex}.png"
            filepath = os.path.join(settings.MEDIA_ROOT, filename)
            fig.savefig(filepath, bbox_inches='tight')
            plt.close(fig)
            print(f"MEDIA_ROOT = {settings.MEDIA_ROOT}")
            return settings.MEDIA_URL + filename

        # Plot 1: Indicator levels
        fig1 = plt.figure(figsize=(8, 5))
        for _, row in df_output.iterrows():
            plt.plot(row[list(range(T))], color=row.color, linewidth=3)
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['top'].set_visible(False)
        plt.xlim(0, T)
        plt.xlabel('time')
        plt.ylabel('indicator level')
        plot_urls.append(save_plot(fig1))

        # Plot 2: Change from initial
        fig2 = plt.figure(figsize=(8, 5))
        for _, row in df_output.iterrows():
            plt.plot(row[list(range(T))] - row[0], color=row.color, linewidth=3)
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['top'].set_visible(False)
        plt.xlim(0, T)
        plt.xlabel('time')
        plt.ylabel('change w.r.t initial condition')
        plot_urls.append(save_plot(fig2))

        # Plot 3: Final levels vs goals
        fig3 = plt.figure(figsize=(14, 5))
        for idx, row in df_output.iterrows():
            plt.bar(idx, row[T - 1], color=row.color, linewidth=3)
            plt.plot([idx, idx], [row[T - 1], row.goal], color=row.color, linewidth=1)
            plt.plot(idx, row.goal, '.', mec='w', mfc=row.color, markersize=15)
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['top'].set_visible(False)
        plt.xlim(-1, N)
        plt.xticks(range(N))
        plt.gca().set_xticklabels(df_output.indicator_label, rotation=90)
        plt.xlabel('indicator')
        plt.ylabel('level')
        plot_urls.append(save_plot(fig3))

        # Save to session and redirect to results
        request.session['plots'] = plot_urls
        request.session['simulation_table_html'] = df_output.to_html(index=False)
        request.session.modified = True

        return redirect('results')

    except Exception as e:
        messages.error(request, f"Simulation error: {e}")
        return redirect('simulation')
    


def results(request):
    plots = request.session.get('plots', [])
    table_html = request.session.get('simulation_table_html', '')

    if not plots or not table_html:
        return render(request, 'results.html', {
            'error': 'No simulation results found. Please run a simulation first.'
        })

    return render(request, 'results.html', {
        'plots': plots,
        'table': table_html,
    })

