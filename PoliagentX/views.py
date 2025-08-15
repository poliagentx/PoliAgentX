
from io import BytesIO
import os
from django.views.decorators.csrf import csrf_exempt
from PoliagentX.backend_poliagentx.policy_priority_inference import calibrate,run_ppi,run_ppi_parallel
from PoliagentX.backend_poliagentx.relational_table import build_relational_table
from PoliagentX.backend_poliagentx.allocation import get_sdg_allocation_from_file
from PoliagentX.backend_poliagentx.budget import expand_budget
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from openpyxl import Workbook
from .forms import *
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.contrib.staticfiles import finders
import pandas as pd
import numpy as np
import tempfile
import matplotlib.pyplot as plt
from openpyxl.utils.dataframe import dataframe_to_rows
import plotly.graph_objects as go


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

        # os.makedirs('clean_data', exist_ok=True)
        # output_path = os.path.join('clean_data', 'data_budget.xlsx')
        # df_exp.to_excel(output_path, index=False)
        
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

            # os.makedirs('clean_data', exist_ok=True)
            # output_path = os.path.join('clean_data', 'network.xlsx')
            # data_net.to_excel(output_path, index=False)
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
        uploaded_budget_path = request.session.get('budget_file_path')
        
        try:
            threshold = float(request.POST.get('threshold', 0.7))
        except (ValueError, TypeError):
            threshold = 0.7

        parameters = run_calibration(request, threshold=threshold)
        parameters = pd.DataFrame(parameters)
        
       

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        tmp_file.close()  # close it so ExcelWriter can open it by name

        with pd.ExcelWriter(tmp_file.name) as writer:
            parameters.to_excel(writer, sheet_name='template', index=False)
           

        request.session['param_excel_path'] = tmp_file.name
        # return redirect('simulation')
        # os.makedirs('clean_data', exist_ok=True)
        # output_path = os.path.join('clean_data', 'parameter.xlsx')
        # parameters.to_excel(output_path, index=False)

        return render(request, 'calibration.html', {
            'threshold': threshold,
            'parameters': parameters
                
        })
        
def run_simulation(request):
    # import pandas as pd
    # import numpy as np
    # import plotly.graph_objs as go
    from django.shortcuts import render, redirect

    # --- Load paths from session ---
    indicators_path = request.session.get('indicators_path')
    network_path = request.session.get('network_path')
    budget_path = request.session.get('budget_file_path')

    if not all([indicators_path, network_path, budget_path]):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "Missing required files for simulation.")
        return redirect('calibration')

    # --- Load simulation output or indicators ---
    df_output = pd.read_excel(indicators_path)

    # Ensure color column exists
    if 'color' not in df_output.columns:
        df_output['color'] = 'blue'

    # Identify timestep columns dynamically
    time_columns = [c for c in df_output.columns if c not in ['indicator_label','color']]
    df_output[time_columns] = df_output[time_columns].apply(pd.to_numeric, errors='coerce')
    n_steps = len(time_columns)

    # Generate random goals dynamically
    I0 = df_output[time_columns[0]]
    Imax = df_output[time_columns].max(axis=1)
    goals = np.random.rand(len(df_output)) * (Imax - I0) + I0
    df_output['goal'] = goals

    plot_htmls = []

    # --------------------
    # 1. Indicator Levels Over Time (lines)
    frames1 = []
    for step, col in enumerate(time_columns):
        frames1.append(go.Frame(
            data=[go.Scatter(
                x=df_output['indicator_label'],
                y=df_output[col],
                mode="lines+markers",
                marker=dict(color=df_output['color'])
            )],
            name=str(step)
        ))
    fig1 = go.Figure(
        data=frames1[0].data,
        layout=go.Layout(
            title="Indicator Levels Over Time",
            xaxis_title="Indicator",
            yaxis_title="Level",
            yaxis=dict(range=[0, df_output[time_columns].max().max() * 1.1]),
            updatemenus=[dict(
                type="buttons",
                buttons=[
                    dict(label="Play", method="animate",
                         args=[None, {"frame": {"duration": 300, "redraw": True}}]),
                    dict(label="Pause", method="animate",
                         args=[[None], {"frame": {"duration": 0, "redraw": False}}])
                ]
            )]
        ),
        frames=frames1
    )
    plot_htmls.append(fig1.to_html(full_html=False, include_plotlyjs='cdn'))

    # --------------------
    # 2. Change from Initial Over Time (bars)
    df_change = df_output.copy()
    for col in time_columns:
        df_change[col] = df_change[col] - df_change[time_columns[0]]

    frames2 = []
    for step, col in enumerate(time_columns):
        frames2.append(go.Frame(
            data=[go.Bar(
                x=df_change['indicator_label'],
                y=df_change[col],
                marker_color=df_change['color']
            )],
            name=str(step)
        ))
    fig2 = go.Figure(
        data=frames2[0].data,
        layout=go.Layout(
            title="Change from Initial Over Time",
            xaxis_title="Indicator",
            yaxis_title="Change",
            yaxis=dict(
                range=[df_change[time_columns].min().min() * 1.1,
                       df_change[time_columns].max().max() * 1.1]
            ),
            updatemenus=[dict(
                type="buttons",
                buttons=[
                    dict(label="Play", method="animate",
                         args=[None, {"frame": {"duration": 300, "redraw": True}}]),
                    dict(label="Pause", method="animate",
                         args=[[None], {"frame": {"duration": 0, "redraw": False}}])
                ]
            )]
        ),
        frames=frames2
    )
    plot_htmls.append(fig2.to_html(full_html=False, include_plotlyjs=False))

    # --------------------
    # 3. Final Levels vs Goals (animated bar growth)
    final_levels = df_output[time_columns[-1]]
    indicators = df_output['indicator_label']
    colors = df_output['color']

    frames3 = []
    for step in range(n_steps + 1):
        fraction = step / n_steps
        frames3.append(go.Frame(
            data=[
                go.Bar(
                    x=indicators,
                    y=final_levels * fraction,
                    marker_color=colors,
                    name="Final level"
                ),
                go.Scatter(
                    x=indicators,
                    y=df_output['goal'],
                    mode="markers",
                    marker=dict(size=12, color=colors, symbol='circle-open'),
                    name="Goal",
                    opacity=fraction
                )
            ],
            name=str(step)
        ))

    fig3 = go.Figure(
        data=frames3[0].data,
        layout=go.Layout(
            title="Final Levels vs Goals",
            xaxis_title="Indicator",
            yaxis_title="Level",
            yaxis=dict(range=[0, max(final_levels.max(), df_output['goal'].max()) * 1.1]),
            updatemenus=[dict(
                type="buttons",
                buttons=[
                    dict(label="Play", method="animate",
                         args=[None, {"frame": {"duration": 300, "redraw": True}}]),
                    dict(label="Pause", method="animate",
                         args=[[None], {"frame": {"duration": 0, "redraw": False}}])
                ]
            )]
        ),
        frames=frames3
    )
    plot_htmls.append(fig3.to_html(full_html=False, include_plotlyjs=False))

    # --------------------
    # Save to session and redirect
    request.session['plots_html'] = plot_htmls
    request.session['simulation_table_html'] = df_output.to_html(index=False)
    request.session.modified = True
    try:
        return redirect('results')
    except Exception as e:
        print(f"Error occurred while redirecting: {e}")
        return render(request, 'error.html', {'error': str(e)})


def results(request):
    plot_data = request.session.get('plots_html', [])
    table_data = request.session.get('simulation_table_html', [])

    if not plot_data or not table_data:
        return render(request, 'results.html', {
            'error': 'No simulation results found. Please run a simulation first.'
        })

    return render(request, 'results.html', {
        'plot_data': plot_data,
        'table_data': table_data,
    })