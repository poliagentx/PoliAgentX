import tempfile
import io
import os
from django.conf import settings
import uuid
from django.views.decorators.csrf import csrf_exempt
from PoliagentX.backend_poliagentx.policy_priority_inference import calibrate
from PoliagentX.backend_poliagentx.relational_table import build_relational_table
from PoliagentX.backend_poliagentx.allocation import get_sdg_allocation_from_file,SDG_ALLOCATION
from PoliagentX.backend_poliagentx.budget import expand_budget
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from PoliagentX.backend_poliagentx.simple_prospective_simulation import run_simulation
from PoliagentX.backend_poliagentx.structural_bottlenecks import analyze_structural_bottlenecks
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
            os.makedirs('clean_data', exist_ok=True)
            output_path = os.path.join('clean_data', 'data_indicators.xlsx')
            df.to_excel(output_path, index=False)

            # Store cleaned path in session
            request.session['indicators_path'] = output_path

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
        
        # 1️⃣ Handle uploaded Excel file first
        if 'government_expenditure' in request.FILES:
            upload_form = Uploaded_Budget(request.POST, request.FILES)
            if upload_form.is_valid():
                uploaded_file = request.FILES['government_expenditure']
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                        for chunk in uploaded_file.chunks():
                            tmp.write(chunk)
                        tmp_path = tmp.name

                    data_exp = pd.read_excel(tmp_path)
                    data_indi = pd.read_excel(indicators_path)

                    # Filter for matching & instrumental SDGs
                    data_exp = data_exp[data_exp.sdg.isin(data_indi.sdg.values)]
                    data_exp = data_exp[data_exp.sdg.isin(data_indi[data_indi.instrumental == 1].sdg.values)]

                    if 'sdg' not in data_exp.columns:
                        messages.error(request, "❌ Uploaded file must have an 'sdg' column.")
                        return redirect('budgets_page')

            
                    df_exp = expand_budget(data_exp)

                except Exception as e:
                    messages.error(request, f"❌ Failed to read uploaded file: {e}")
                    return redirect('budgets_page')
            else:
                messages.error(request, "❌ Invalid file upload.")
                return redirect('budgets_page')
            
            df_rel = build_relational_table(data_indi)
           

        # 2️⃣ If no file, handle manual budget input
        elif 'budget' in request.POST:
            budget_form = BudgetForm(request.POST)
            if budget_form.is_valid():
                budget = budget_form.cleaned_data['budget']
                inflation = budget_form.cleaned_data['inflation_rate']
                adjusted_budget = budget / (1 + (inflation / 100))
                data_indi = pd.read_excel(indicators_path)

                years = sorted([int(col) for col in data_indi.columns if str(col).isdigit()])
                periods = len(years)

                data_exp = pd.DataFrame([
                    {
                        'sdg': i + 1,
                        **{
                            str(years[0] + j): round(adjusted_budget * sdg['percent'] / 100 / periods, 2)
                            for j in range(periods)
                        }
                    }
                    for i, sdg in enumerate(allocation)
                ])
                
                data_exp = data_exp[data_exp.sdg.isin(data_indi.sdg.values)]
                data_exp = data_exp[data_exp.sdg.isin(data_indi[data_indi.instrumental == 1].sdg.values)]

                if 'sdg' not in data_exp.columns:
                    messages.error(request, "❌ Uploaded file must have an 'sdg' column.")
                    return redirect('budgets_page')

                df_exp = expand_budget(data_exp)

            else:
                messages.error(request, "❌ Invalid manual budget input.")
                return redirect('budgets_page')
            
            
            df_rel = build_relational_table(data_indi)
           

        # 3️⃣ Save results if `data_exp` exists
        if data_exp is not None:
    
            # Create a new workbook
            wb = Workbook()

            # --- Sheet 1: template_budget ---
            ws_budget = wb.active
            ws_budget.title = "template_budget"
            for r in dataframe_to_rows(df_exp, index=False, header=True):
                ws_budget.append(r)

            # --- Sheet 2: relational_table ---
            ws_relation = wb.create_sheet(title="relational_table")
            for r in dataframe_to_rows(df_rel, index=False, header=True):
                ws_relation.append(r)

            # Save to temp file and store path in session
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                wb.save(tmp_file.name)
                request.session['budget_file_path'] = tmp_file.name
            messages.success(request, "☑️ Budget processed successfully.")

    return render(request, 'budgets.html', {
        'budget_form': budget_form,
        'upload_form': upload_form,
    })


def upload_network(request):
    
    if request.method == 'POST':
        skip_indicators = request.POST.get('skip_indicators', 'off') == 'on'
        form = Uploaded_networks(request.POST, request.FILES)

        file_to_process_path = None
        delete_temp_after_use = False

        # Case 1: User chooses to skip network processing
        if skip_indicators:
            if not os.path.exists('clean_data/data_network.csv'):
                # messages.error(request, "❌ Skipping network processing failed: No existing network data found.")
                return render(request, 'Network.html', {'form': form})
            # messages.success(request, "☑️ Skipped network processing. Using existing network data.")
            return render(request, 'Network.html', {'form': Uploaded_networks()})

        # Case 2: User uploads a new file for network processing
        uploaded_file = request.FILES.get('interdependency_network')
       
        if uploaded_file and form.is_valid():
            # Save uploaded file temporarily
            os.makedirs('temp', exist_ok=True)
            temp_file_name = uploaded_file.name
            # Ensure unique temp file name to avoid conflicts if multiple users upload same filename
            temp_file_path = os.path.join('temp', f"{os.urandom(8).hex()}_{temp_file_name}")

            with open(temp_file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            file_to_process_path = temp_file_path
            delete_temp_after_use = True
            messages.success(request, "☑️ File uploaded successfully. Processing network data...")

        # Case 3: No new file uploaded, try to use previously prepared indicator data
        elif not uploaded_file and request.session.get('indicators_path'):
            file_to_process_path = request.session.get('indicators_path')
            # No need to set delete_temp_after_use = True as this file was prepared by another function
            messages.info(request, "ℹ️ No new file uploaded. Using previously prepared indicator data for network processing.")
        else:
            # If no file uploaded, not skipping, and no prepared indicator path
            # messages.error(request, "❌ Please upload a network file or ensure prepared indicator data is available.")
            return render(request, 'Network.html', {'form': form})

        # --- Common processing logic for both new uploads and prepared data ---
        if file_to_process_path:
            # Load Excel data
            try:
                data = pd.read_excel(file_to_process_path)
            except Exception as e:
                messages.error(request, f"❌ Failed to read Excel file from '{file_to_process_path}': {str(e)}")
                if delete_temp_after_use and os.path.exists(file_to_process_path):
                    os.remove(file_to_process_path)
                return render(request, 'Network.html', {'form': form})
            finally:
                # Clean up the temporary file if it was created in this function
                if delete_temp_after_use and os.path.exists(file_to_process_path):
                    os.remove(file_to_process_path)

            # Begin matrix processing
            N = len(data)
            M = np.zeros((N, N))

            # Find year columns
            years = [col for col in data.columns if str(col).isnumeric()]

            # Ensure there are enough years for calculating changes
            if len(years) < 2:
                # messages.error(request, "❌ Not enough year columns to calculate network correlations. Need at least two years.")
                return render(request, 'Network.html', {'form': form})


            for i, rowi in data.iterrows():
                for j, rowj in data.iterrows():
                    if i != j:
                        # Ensure the series have enough data points for change calculation
                        if len(rowi[years].values) < 2 or len(rowj[years].values) < 2:
                            continue # Skip if not enough data points

                        serie1 = rowi[years].values.astype(float)
                        serie2 = rowj[years].values.astype(float)

                        change_serie1 = serie1[1:] - serie1[:-1]
                        change_serie2 = serie2[1:] - serie2[:-1]

                        # Check if there's any variation in the change series
                        # np.all(change_serie == change_serie[0]) checks if all elements are the same
                        if not (np.all(change_serie1 == change_serie1[0]) or np.all(change_serie2 == change_serie2[0])):
                            corr = np.corrcoef(change_serie1, change_serie2)[0, 1]
                            if not np.isnan(corr):
                                M[i, j] = corr

            M[np.abs(M) < 0.5] = 0

            # Build edge list
            # Ensure 'indicator_label' column exists in the DataFrame
            if 'indicator_label' not in data.columns:
                messages.error(request, "❌ Missing 'indicator_label' column in the uploaded data. Cannot build network.")
                return render(request, 'Network.html', {'form': form})

            ids = data['indicator_label'].values
            edge_list = []
            for i, j in zip(*np.where(M != 0)):
                edge_list.append([ids[i], ids[j], M[i, j]])

            # Save result to Excel
            os.makedirs('clean_data', exist_ok=True)
            output_path = os.path.join('clean_data', 'data_network.xlsx')
            pd.DataFrame(edge_list, columns=['origin', 'destination', 'weight']) \
                .to_excel(output_path, index=False)
                
            request.session['network_path'] = output_path

            # messages.success(request, "☑️ File processed and network created.")
            return render(request, 'Network.html', {'form': Uploaded_networks()})

    # GET request
    return render(request, 'Network.html', {'form': Uploaded_networks()})

def calibration(request):
    return render(request,'calibration.html')
def simulation(request):
    return render(request,'simulation.html')


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
    relation_path = request.session.get('relation_file_path')

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
        
        # if not uploaded_budget_path:
        #     messages.error(request, "❌ Budget not found in session. Please upload or generate a budget.")
        #     return redirect('budgets_page')

        try:
            threshold = float(request.POST.get('threshold', 0.7))
        except (ValueError, TypeError):
            threshold = 0.7

        parameters = run_calibration(request, threshold=threshold)

        return render(request, 'calibration.html', {
            'threshold': threshold,
            'parameters': parameters
        })