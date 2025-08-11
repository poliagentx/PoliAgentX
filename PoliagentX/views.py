import tempfile
from io import BytesIO
import io
import os
from django.conf import settings
import uuid
from django.views.decorators.csrf import csrf_exempt
from backend_poliagentx.policy_priority_inference import calibrate
from django.contrib import messages
from django.http import FileResponse, HttpResponse
# from PoliagentX.backend_poliagentx.model_calibration import load_uploaded_data
from backend_poliagentx.simple_prospective_simulation import run_simulation
from backend_poliagentx.structural_bottlenecks import analyze_structural_bottlenecks
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
                data_filtered = data.copy()  # don't drop anything here
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
            df['seriesCode'] = data['seriesCode']
            df['sdg'] = data['sdg']
            df['min_value'] = 0
            df['max_value'] = 1
            df['instrumental'] = data['instrumental']
            df['seriesName'] = data['seriesName']
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
            df['qm'] = -0.33
            df['rl'] = -0.33
            

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

# from datetime import datetime
# def budgets_page(request):
#     indicators_path = request.session.get('indicators_path')

#     if not indicators_path:
#         messages.error(request, "Indicators file is missing. Please upload it first.")
#         return redirect('upload_indicators')

#     allocation = get_sdg_allocation_from_file(indicators_path)
#     budget_form = BudgetForm()
#     upload_form = Uploaded_Budget()
#     data_exp = None

#     if request.method == 'POST':
#         data_indi = pd.read_excel(indicators_path)

#         # Handle uploaded Excel file
#         if 'government_expenditure' in request.FILES:
#             upload_form = Uploaded_Budget(request.POST, request.FILES)
#             if not upload_form.is_valid():
#                 messages.error(request, "❌ Invalid file upload.")
#                 return redirect('budgets_page')

#             uploaded_file = request.FILES['government_expenditure']

#             try:
#                 data_exp = pd.read_excel(uploaded_file)

#                 if 'sdg' not in data_exp.columns:
#                     messages.error(request, "❌ Uploaded file must have an 'sdg' column.")
#                     return redirect('budgets_page')

#                 data_exp = data_exp[data_exp.sdg.isin(data_indi.sdg.values)]
#                 data_exp = data_exp[data_exp.sdg.isin(data_indi[data_indi.instrumental == 1].sdg.values)]

#             except Exception as e:
#                 messages.error(request, f"❌ Failed to read uploaded file: {e}")
#                 return redirect('budgets_page')

#         # Handle manual budget input
#         elif 'budget' in request.POST:
#             budget_form = BudgetForm(request.POST)
#             if not budget_form.is_valid():
#                 messages.error(request, "❌ Invalid manual budget input.")
#                 return redirect('budgets_page')

#             budget = budget_form.cleaned_data['budget']
#             inflation = budget_form.cleaned_data['inflation_rate']
#             adjusted_budget = budget / (1 + (inflation / 100))

#             years = sorted([int(col) for col in data_indi.columns if str(col).isdigit()])
#             periods = len(years)

#             data_exp = pd.DataFrame([
#                 {
#                     'sdg': i + 1,
#                     **{
#                         str(years[0] + j): round(adjusted_budget * sdg['percent'] / 100 / periods, 2)
#                         for j in range(periods)
#                     }
#                 }
#                 for i, sdg in enumerate(allocation)
#             ])

#             if 'sdg' not in data_exp.columns:
#                 messages.error(request, "❌ Data is missing an 'sdg' column.")
#                 return redirect('budgets_page')

#             data_exp = data_exp[data_exp.sdg.isin(data_indi.sdg.values)]
#             data_exp = data_exp[data_exp.sdg.isin(data_indi[data_indi.instrumental == 1].sdg.values)]

#         else:
#             # No file and no manual budget input
#             return render(request, 'budgets.html', {
#                 'budget_form': budget_form,
#                 'upload_form': upload_form,
#             })

#         # Now expand and build relational table
#         df_exp = expand_budget(data_exp)
#         df_rel = build_relational_table(data_indi)

#         # Save results
#         save_dir = 'clean_data'
#         os.makedirs(save_dir, exist_ok=True)

#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = f"budget_allocation_{timestamp}.xlsx"
#         file_path = os.path.join(save_dir, filename)

#         with pd.ExcelWriter(file_path) as writer:
#             df_exp.to_excel(writer, sheet_name='template_budget', index=False)
#             df_rel.to_excel(writer, sheet_name='relational_table', index=False)

#         request.session['budget_file_path'] = file_path
#         return redirect('upload_network')

#     return render(request, 'budgets.html', {
#         'budget_form': budget_form,
#         'upload_form': upload_form,
#     })
# from django.conf import settings
# import logging
# logger = logging.getLogger(__name__)
# from pathlib import Path
# def upload_network(request):
#     indicators_path = request.session.get('indicators_path')
#     if not indicators_path:
#         messages.error(request, "Indicators file is missing. Please upload it first.")
#         return redirect('upload_indicators')

#     skip_form = Skip_networks()
#     uploaded_form = Uploaded_networks()
#     data_net = None

#     if request.method == 'POST':
#         print("POST request received")

#         if 'interdependency_network' in request.FILES:
#             print("Uploaded file detected")
#             uploaded_form = Uploaded_networks(request.POST, request.FILES)
#             if uploaded_form.is_valid():
#                 uploaded_file = request.FILES['interdependency_network']
#                 try:
#                     data_net = pd.read_excel(uploaded_file)
#                     print("Uploaded file read successfully")
#                 except Exception as e:
#                     print(f"Error reading uploaded file: {e}")
#                     messages.error(request, f"❌ Failed to read uploaded file: {e}")
#                     return redirect('upload_network')
#             else:
#                 print("Uploaded form invalid:", uploaded_form.errors)
#                 messages.error(request, "Uploaded file form is invalid.")
#                 return redirect('upload_network')

#         elif 'skip-network' in request.POST:
#             print("Skip network requested")
#             skip_form = Skip_networks(request.POST)
#             if skip_form.is_valid():
#                 print("Skip form valid, generating synthetic network")
#                 data_indi = pd.read_excel(indicators_path)
#                 years = sorted([col for col in data_indi.columns if str(col).strip().isdigit()])
#                 data_array = data_indi[years].astype(float).values

#                 change_serie1_all = data_array[:, 2:] - data_array[:, 1:-1]
#                 change_serie2_all = data_array[:, 1:-1] - data_array[:, :-2]

#                 def is_not_constant(arr):
#                     return np.any(arr != arr[0])

#                 valid_c1 = np.array([is_not_constant(row) for row in change_serie1_all])
#                 valid_c2 = np.array([is_not_constant(row) for row in change_serie2_all])

#                 N = len(data_indi)
#                 M = np.zeros((N, N))

#                 valid_i = np.where(valid_c1)[0]
#                 valid_j = np.where(valid_c2)[0]

#                 for i in valid_i:
#                     c1 = change_serie1_all[i]
#                     for j in valid_j:
#                         if i != j:
#                             c2 = change_serie2_all[j]
#                             M[i, j] = np.corrcoef(c1, c2)[0, 1]

#                 M[np.abs(M) < 0.5] = 0

#                 ids = data_indi.indicator_label.values
#                 edge_list = [[ids[i], ids[j], M[i, j]] for i, j in zip(*np.where(M != 0))]
#                 data_net = pd.DataFrame(edge_list, columns=['origin', 'destination', 'weight'])

#                 print("Synthetic network generated")
#             else:
#                 print("Skip form invalid:", skip_form.errors)
#                 messages.error(request, "Skip form is invalid.")
#                 return redirect('upload_network')

#         if data_net is not None:
#             print("Saving network data to temporary file and session")

#             wb = Workbook()
#             ws_network = wb.active
#             ws_network.title = "template_network"
#             for r in dataframe_to_rows(data_net, index=False, header=True):
#                 ws_network.append(r)

#             with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
#                 wb.save(tmp_file.name)
#                 request.session['network_path'] = tmp_file.name
#                 print(f"Temporary file saved at {tmp_file.name}")

#             clean_dir = Path(settings.BASE_DIR) / 'clean_data'
#             clean_dir.mkdir(parents=True, exist_ok=True)
#             output_path = clean_dir / 'data_network.xlsx'
#             data_net.to_excel(output_path, index=False)
#             print(f"Network data saved locally at {output_path}")

#         return redirect('calibration')

#     return render(request, 'Network.html', {
#         'skip_form': skip_form,
#         'uploaded_form': uploaded_form,
#     })


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
        uploaded_budget_path = request.session.get('budget_file_path')
        
        try:
            threshold = float(request.POST.get('threshold', 0.7))
        except (ValueError, TypeError):
            threshold = 0.7

        parameters = run_calibration(request, threshold=threshold)
        
       

        # print("Calibration parameters saved to Excel file at:")
       
        
        param_excel_path = save_parameters_to_excel(parameters)
        old_path = request.session.get('param_excel_path')
    
        # print(param_excel_path)
        
        # Delete old temp file if exists
        if old_path and os.path.exists(old_path):
            os.remove(old_path)

        request.session['param_excel_path'] = param_excel_path


        return render(request, 'calibration.html', {
            'threshold': threshold,
            'parameters': parameters
                
        })
        
    