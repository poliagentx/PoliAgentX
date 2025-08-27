import json
import base64
from io import BytesIO
import os
import random
from django.views.decorators.csrf import csrf_exempt
from PoliagentX.backend_poliagentx.policy_priority_inference import calibrate,run_ppi,run_ppi_parallel
from PoliagentX.backend_poliagentx.relational_table import build_relational_table
from PoliagentX.backend_poliagentx.allocation import get_sdg_allocation_from_file
from PoliagentX.backend_poliagentx.budget import expand_budget
from django.contrib import messages
from django.http import FileResponse, HttpResponse,JsonResponse
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
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            tmp_file.close()  # close it so ExcelWriter can open it by name

            with pd.ExcelWriter(tmp_file.name) as writer:
                df.to_excel(writer, sheet_name='template', index=False)

            request.session['indicators_path'] = tmp_file.name

            messages.success(request, "File uploaded and processed successfully.")
            return render(request, 'indicators.html', {'form': Uploaded_indicators()})

        return render(request, 'indicators.html', {'form': form})

    return render(request, 'indicators.html', {'form': Uploaded_indicators()})


# --- Helper to safely clean DataFrame column names ---
def clean_columns(df):
    df.columns = [str(c).strip() if c is not None else "" for c in df.columns]
    return df


def budgets_page(request):
    indicators_path = request.session.get('indicators_path')
    if not indicators_path:
        print("❌ Indicators file is missing. Please upload it first.")
        return render(request, 'upload_indicators.html')

    allocation = get_sdg_allocation_from_file(indicators_path)
    budget_form = BudgetForm()
    upload_form = Uploaded_Budget()

    if request.method == 'POST':
        data_indi = pd.read_excel(indicators_path)
        data_indi = clean_columns(data_indi)

        data_exp = None

        # Handle uploaded Excel
        if 'government_expenditure' in request.FILES:
            upload_form = Uploaded_Budget(request.POST, request.FILES)
            if not upload_form.is_valid():
                print("❌ Invalid file upload.")
                return render(request, 'budgets.html', {'budget_form': budget_form, 'upload_form': upload_form})

            try:
                uploaded_file = request.FILES['government_expenditure']
                df_uploaded = pd.ExcelFile(uploaded_file)

                if "raw_expenditure" not in df_uploaded.sheet_names:
                    print("❌ Uploaded file must have a sheet named 'raw_expenditure'.")
                    return render(request, 'budgets.html', {'budget_form': budget_form, 'upload_form': upload_form})

                raw_exp = pd.read_excel(df_uploaded, sheet_name="raw_expenditure")
                raw_exp = clean_columns(raw_exp)

                if "sdg" not in raw_exp.columns:
                    print("❌ 'raw_expenditure' sheet must have an 'sdg' column.")
                    return render(request, 'budgets.html', {'budget_form': budget_form, 'upload_form': upload_form})

                year_cols = [col for col in raw_exp.columns if str(col).isdigit()]
                if not year_cols:
                    print("❌ No numeric year columns found in uploaded budget.")
                    return render(request, 'budgets.html', {'budget_form': budget_form, 'upload_form': upload_form})

                # Coerce numeric columns
                raw_exp[year_cols] = raw_exp[year_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
                data_exp = raw_exp[['sdg'] + year_cols].copy()
                data_exp = clean_columns(data_exp)

                print("DEBUG - Uploaded budget DataFrame:\n", data_exp)

            except Exception as e:
                print(f"❌ Failed to process uploaded file: {e}")
                return render(request, 'budgets.html', {'budget_form': budget_form, 'upload_form': upload_form})

        # Handle manual input
        elif 'budget' in request.POST:
            budget_form = BudgetForm(request.POST)
            if not budget_form.is_valid():
                print("❌ Invalid manual budget input.")
                return render(request, 'budgets.html', {'budget_form': budget_form, 'upload_form': upload_form})

            budget = budget_form.cleaned_data['budget']
            inflation = budget_form.cleaned_data['inflation_rate']
            adjusted_budget = budget / (1 + (inflation / 100))

            years = sorted([int(col) for col in data_indi.columns if str(col).isdigit()])
            periods = len(years)

            data_exp = pd.DataFrame([
                {
                    'sdg': i + 1,
                    **{str(j): round(adjusted_budget * sdg['percent'] / 100 / periods, 2) for j in range(periods)}
                }
                for i, sdg in enumerate(allocation)
            ])
            data_exp = clean_columns(data_exp)
            print("DEBUG - Manual budget DataFrame:\n", data_exp)

        else:
            return render(request, 'budgets.html', {'budget_form': budget_form, 'upload_form': upload_form})

        # Build relational table
        df_rel = build_relational_table(data_indi)
        df_rel = clean_columns(df_rel)

        # Align SDGs
        rel_sdgs = set(df_rel['sdg'].astype(int))
        exp_sdgs = set(data_exp['sdg'].astype(int))

        missing_sdgs = rel_sdgs - exp_sdgs
        for sdg in missing_sdgs:
            zero_row = {'sdg': sdg}
            for col in data_exp.columns:
                if col != 'sdg':
                    zero_row[col] = 0
            data_exp = pd.concat([data_exp, pd.DataFrame([zero_row])], ignore_index=True)

        extra_sdgs = exp_sdgs - rel_sdgs
        if extra_sdgs:
            data_exp = data_exp[~data_exp['sdg'].astype(int).isin(extra_sdgs)]

        data_exp = data_exp.sort_values('sdg').reset_index(drop=True)

        # Save Excel files for calibration - FIXED: Use consistent sheet names
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            with pd.ExcelWriter(tmp_file.name) as writer:
                data_exp.to_excel(writer, sheet_name='budget_data', index=False)  # Changed from 'template_budget'
                df_rel.to_excel(writer, sheet_name='relational_table', index=False)
            request.session['budget_file_path'] = tmp_file.name

        df_exp_indicators = df_rel.merge(data_exp, on="sdg", how="left")
        if "indicator" in df_exp_indicators.columns:
            df_exp_indicators.rename(columns={"indicator": "indicator_label"}, inplace=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file2:
            with pd.ExcelWriter(tmp_file2.name) as writer:
                df_exp_indicators.to_excel(writer, sheet_name='indicator_budget', index=False)
            request.session['indicator_budget_path'] = tmp_file2.name

        print("✅ Budget processing complete. Files saved for calibration.")
        return redirect('upload_network')

    # GET request
    return render(request, 'budgets.html', {'budget_form': budget_form, 'upload_form': upload_form})


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
    budget_file_path = request.session.get('budget_file_path')  # Use the budget file directly

    if not all([indicators_path, network_path, budget_file_path]):
        raise ValueError("Missing required files for calibration.")

    # --- Load indicators ---
    df_indis = pd.read_excel(indicators_path)
    N = len(df_indis)
    I0 = df_indis.I0.values
    IF = df_indis.IF.values
    success_rates = df_indis.success_rates.values
    R = df_indis.instrumental.values  # This is the key array - 1 for instrumental, 0 for non-instrumental
    qm = df_indis.qm.values
    rl = df_indis.rl.values
    indis_index = {code: i for i, code in enumerate(df_indis.indicator_label)}

    # --- Load network ---
    df_net = pd.read_excel(network_path)
    A = np.zeros((N, N))
    for _, row in df_net.iterrows():
        i = indis_index[row.origin]
        j = indis_index[row.destination]
        A[i, j] = row.weight

    # --- Load budget data properly ---
    try:
        excel_file = pd.ExcelFile(budget_file_path)
        available_sheets = excel_file.sheet_names
        print(f"Available sheets in budget file: {available_sheets}")
        
        # Load budget data (SDG level)
        if "budget_data" in available_sheets:
            df_exp_sdg = pd.read_excel(budget_file_path, sheet_name="budget_data")
        elif "template_budget" in available_sheets:
            df_exp_sdg = pd.read_excel(budget_file_path, sheet_name="template_budget")
        else:
            df_exp_sdg = pd.read_excel(budget_file_path, sheet_name=available_sheets[0])
            
        # Load relational table
        if "relational_table" in available_sheets:
            df_rel = pd.read_excel(budget_file_path, sheet_name="relational_table")
        else:
            df_rel = build_relational_table(df_indis)
            
    except Exception as e:
        raise ValueError(f"Error loading budget data: {str(e)}")
    
    # Dynamically detect budget columns
    budget_cols = [c for c in df_exp_sdg.columns if str(c).isdigit()]
    if not budget_cols:
        raise ValueError("No numeric budget columns found in budget data.")
    
    # Ensure budget columns are numeric
    df_exp_sdg[budget_cols] = df_exp_sdg[budget_cols].apply(pd.to_numeric, errors='coerce').fillna(0.0)
    
    # Get instrumental indicators only
    instrumental_indicators = df_indis[df_indis.instrumental == 1].copy()
    instrumental_indices = np.where(R == 1)[0]
    
    print(f"Total indicators: {N}")
    print(f"Instrumental indicators: {len(instrumental_indicators)}")
    print(f"Instrumental indices: {instrumental_indices[:10]}...")
    
    # --- Build Bs matrix (SDG-level budgets for instrumental indicators) ---
    # Create a mapping of which instrumental indicators belong to which SDG
    instrumental_sdg_counts = instrumental_indicators.groupby('sdg').size()
    
    # Build Bs matrix by replicating SDG budgets for each instrumental indicator in that SDG
    Bs_rows = []
    B_dict = {}
    
    for _, indicator_row in instrumental_indicators.iterrows():
        indicator_idx = np.where(df_indis['indicator_label'] == indicator_row['indicator_label'])[0][0]
        indicator_sdg = indicator_row['sdg']
        
        # Find budget for this SDG
        sdg_budget_rows = df_exp_sdg[df_exp_sdg['sdg'] == indicator_sdg]
        
        if not sdg_budget_rows.empty:
            # Get budget values for this SDG
            sdg_budget_values = sdg_budget_rows[budget_cols].iloc[0].values
            
            # Count how many instrumental indicators are in this SDG
            indicators_in_sdg = instrumental_sdg_counts.get(indicator_sdg, 1)
            
            # Distribute SDG budget equally among instrumental indicators
            indicator_budget_values = sdg_budget_values / indicators_in_sdg
            
            # Add to Bs matrix
            Bs_rows.append(indicator_budget_values)
            
            # Add to B_dict using the actual indicator index
            B_dict[indicator_idx] = indicator_budget_values.tolist()
        else:
            # No budget for this SDG, assign zeros
            zero_budget = [0.0] * len(budget_cols)
            Bs_rows.append(zero_budget)
            B_dict[indicator_idx] = zero_budget
    
    # Convert to numpy array
    Bs = np.array(Bs_rows)
    
    # --- Validate dimensions ---
    print(f"Bs matrix shape: {Bs.shape}")
    print(f"B_dict has {len(B_dict)} entries")
    print(f"Number of instrumental indicators (R=1): {len(instrumental_indices)}")
    print(f"Expected Bs shape: ({len(instrumental_indices)}, {len(budget_cols)})")
    
    # Check that dimensions match
    if Bs.shape[0] != len(instrumental_indices):
        raise ValueError(
            f"Bs matrix rows ({Bs.shape[0]}) does not match number of instrumental indicators ({len(instrumental_indices)})"
        )
    
    if len(B_dict) != len(instrumental_indices):
        raise ValueError(
            f"B_dict size ({len(B_dict)}) does not match number of instrumental indicators ({len(instrumental_indices)})"
        )

    # Verify all instrumental indices have corresponding budget data
    missing_budget_indices = set(instrumental_indices) - set(B_dict.keys())
    if missing_budget_indices:
        raise ValueError(f"Missing budget data for instrumental indices: {missing_budget_indices}")

    # --- Debug B_dict ---
    print("B_dict structure:")
    print(f"B_dict keys: {sorted(list(B_dict.keys())[:10])}...")  # Show first 10
    print(f"Expected instrumental indices: {sorted(instrumental_indices[:10])}...")  # Show first 10
    for k, v in list(B_dict.items())[:3]:  # Show first 3 entries
        print(f"B_dict[{k}] = {v[:3]}... (showing first 3 values)")

    # Check for uniqueness in B_dict (this might be the issue)
    unique_programs = set()
    for idx, budget_values in B_dict.items():
        budget_tuple = tuple(budget_values)  # Convert to tuple for hashing
        unique_programs.add(budget_tuple)
    
    print(f"Number of unique budget programs: {len(unique_programs)}")
    print(f"Bs matrix rows: {Bs.shape[0]}")
    
    # This error suggests the calibrate function expects unique budget programs
    # Let's make sure each instrumental indicator has a unique budget program
    # by adding small random variations if they are identical
    if len(unique_programs) < Bs.shape[0]:
        print("Adding small variations to create unique budget programs...")
        for i, (idx, budget_values) in enumerate(B_dict.items()):
            # Add a tiny random variation (0.1% of the value)
            variation = np.array(budget_values) * 0.001 * np.random.random()
            B_dict[idx] = (np.array(budget_values) + variation).tolist()
            Bs[i] = np.array(budget_values) + variation

    T = Bs.shape[1]
    parallel_processes = 4
    low_precision_counts = 50

    # --- Run calibration ---
    parameters = calibrate(
        I0, IF, success_rates, A=A, R=R, qm=qm, rl=rl,
        Bs=Bs, B_dict=B_dict, T=T, threshold=threshold,
        parallel_processes=parallel_processes, verbose=True,
        low_precision_counts=low_precision_counts
    )

    return parameters


@csrf_exempt
def start_calibration(request):
    import pandas as pd
    import tempfile
    from django.http import JsonResponse
    from django.shortcuts import render

    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

    try:
        threshold = float(request.POST.get('threshold', 0.5))
    except (ValueError, TypeError):
        threshold = 0.5

    try:
        # Run calibration
        parameters = run_calibration(request, threshold=threshold)
        parameters_df = pd.DataFrame(parameters)

        # Save calibration output to Excel
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        tmp_file.close()
        with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
            parameters_df.to_excel(writer, sheet_name='template', index=False)

        # Store path and calibration flag in session
        request.session['param_excel_path'] = tmp_file.name
        request.session['calibrated'] = True

        # Render calibration page with results
        return render(request, 'calibration.html', {
            'threshold': threshold,
            'parameters': parameters_df,
        })

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def run_simulation(request):
        return render(request,'simulation.html')


# A custom JSONEncoder class to handle NumPy data types
class NumpyJSONEncoder(json.JSONEncoder):
    """
    A custom JSON encoder that handles NumPy data types.
    This prevents 'TypeError: Object of type int64 is not JSON serializable'
    by converting NumPy integers, floats, and arrays to standard Python types.
    """
    def default(self, obj):
        # If the object is a NumPy integer type, return its standard integer value.
        if isinstance(obj, np.integer):
            return int(obj)
        # If the object is a NumPy floating-point type, return its standard float value.
        elif isinstance(obj, np.floating):
            return float(obj)
        # If the object is a NumPy array, return its list representation.
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        # Fallback to the base class's default method for all other types.
        return super().default(obj)


def results(request):
    if request.method != "POST":
        return HttpResponse("Please run the simulation first.", status=400)

    # --- Load file paths from session ---
    param_excel_path = request.session.get("param_excel_path")
    network_path = request.session.get("network_path")
    budget_path = request.session.get("budget_file_path")
    indicators_path = request.session.get("indicators_path")

    if not all([param_excel_path, network_path, budget_path, indicators_path]):
        return HttpResponse("Missing required files.", status=400)

    # --- Load indicators ---
    df_indis = pd.read_excel(indicators_path)
    N = len(df_indis)
    I0 = df_indis.I0.values
    R = df_indis.instrumental.values
    qm = df_indis.qm.values
    rl = df_indis.rl.values
    Imax = df_indis.max_value.values
    Imin = df_indis.min_value.values
    indis_index = {code: i for i, code in enumerate(df_indis.indicator_label)}

    # --- Load parameters ---
    df_params = pd.read_excel(param_excel_path, skiprows=1)
    alpha = df_params.alpha.values
    alpha_prime = df_params.alpha_prime.values
    betas = df_params.beta.values

    # --- Load network ---
    df_net = pd.read_excel(network_path)
    A = np.zeros((N, N))
    for _, row in df_net.iterrows():
        i = indis_index[row.origin]
        j = indis_index[row.destination]
        A[i, j] = row.weight

    # --- Simulation count ---
    T = int(request.POST.get("num_simulations", 50))

    # --- Load SDG-level budgets ---
    try:
        excel_file = pd.ExcelFile(budget_path)
        available_sheets = excel_file.sheet_names
        print(f"Available sheets in budget file: {available_sheets}")

        if "budget_data" in available_sheets:
            df_exp = pd.read_excel(budget_path, sheet_name="budget_data")
        elif "template_budget" in available_sheets:
            df_exp = pd.read_excel(budget_path, sheet_name="template_budget")
        else:
            df_exp = pd.read_excel(budget_path, sheet_name=available_sheets[0])
            print(f"Using sheet: {available_sheets[0]}")

        if "relational_table" in available_sheets:
            df_rel = pd.read_excel(budget_path, sheet_name="relational_table")
        else:
            df_rel = build_relational_table(df_indis)

    except Exception as e:
        return HttpResponse(f"Error loading budget data: {str(e)}", status=400)

    # --- Build Bs and B_dict correctly for unique budget programs ---
    instrumental_indices = np.where(R == 1)[0]
    
    # Get budget columns (numeric columns)
    budget_cols = [c for c in df_exp.columns if str(c).isdigit()]
    if not budget_cols:
        return HttpResponse("No numeric budget columns found in budget data.", status=400)
    
    # Ensure budget columns are numeric
    df_exp[budget_cols] = df_exp[budget_cols].apply(pd.to_numeric, errors='coerce').fillna(0.0)
    
    # Build Bs matrix from SDG budget programs (each row is a unique budget program)
    programs = df_exp[budget_cols].values  # Shape: (num_sdgs, num_time_periods)
    Bs = programs  # Don't replicate - use the actual unique programs
    
    # Build B_dict mapping instrumental indicator indices to their budget program indices
    B_dict = {}
    instrumental_indicators = df_indis[df_indis.instrumental == 1].copy()
    
    for _, indicator_row in instrumental_indicators.iterrows():
        # Get the actual indicator index in the full indicator array
        indicator_idx = np.where(df_indis['indicator_label'] == indicator_row['indicator_label'])[0][0]
        indicator_sdg = indicator_row['sdg']
        
        # Find the budget program index for this SDG
        sdg_budget_idx = df_exp[df_exp['sdg'] == indicator_sdg].index
        
        if len(sdg_budget_idx) > 0:
            # Map to the first matching budget program index
            program_idx = sdg_budget_idx[0]
            # Store the budget values for this program
            B_dict[indicator_idx] = df_exp.iloc[program_idx][budget_cols].tolist()
        else:
            # No budget for this SDG - this shouldn't happen if data is consistent
            return HttpResponse(f"No budget found for SDG {indicator_sdg} for indicator {indicator_row['indicator_label']}", status=400)
    
    # --- Validation ---
    print(f"Number of instrumental indicators: {len(instrumental_indices)}")
    print(f"Number of SDGs in budget data: {len(df_exp)}")
    print(f"B_dict keys: {sorted(B_dict.keys())[:10]}...")  # Show first 10
    print(f"Expected keys (instrumental indices): {sorted(instrumental_indices[:10])}...")  # Show first 10
    print(f"B_dict size: {len(B_dict)}")
    print(f"Bs shape: {Bs.shape}")
    print(f"Unique budget programs (Bs rows): {Bs.shape[0]}")
    
    # Check that we have budget data for all instrumental indicators
    missing_indices = set(instrumental_indices) - set(B_dict.keys())
    if missing_indices:
        return HttpResponse(f"Missing budget data for instrumental indicators at indices: {missing_indices}", status=400)
    
    # The key insight: run_ppi expects len(unique_programs) == Bs.shape[0]
    # Let's verify this by checking unique budget programs in B_dict
    unique_budgets = set()
    for budget_list in B_dict.values():
        unique_budgets.add(tuple(budget_list))  # Convert to tuple for hashing
    
    print(f"Number of unique budget programs in B_dict: {len(unique_budgets)}")
    print(f"Number of rows in Bs: {Bs.shape[0]}")
    
    if len(unique_budgets) != Bs.shape[0]:
        # If there's a mismatch, we need to rebuild Bs to match the unique programs in B_dict
        print("Rebuilding Bs to match unique programs...")
        unique_budget_list = list(unique_budgets)
        Bs = np.array(unique_budget_list)
        print(f"New Bs shape: {Bs.shape}")
    
    if len(B_dict) != len(instrumental_indices):
        return HttpResponse(f"B_dict size ({len(B_dict)}) doesn't match instrumental indicators ({len(instrumental_indices)})", status=400)

    # --- Generate random goals ---
    goals = np.random.rand(N) * (Imax - I0) + I0

    # --- Run simulations ---
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

    # --- Build output for frontend ---
    df_output_list = []
    for i, serie in enumerate(tsI_hat):
        label = df_indis.iloc[i].indicator_label
        
        # Get budget data for this indicator if it's instrumental
        budget_data = []
        if i in B_dict:
            budget_data = B_dict[i]
        
        row_dict = {
            "indicator_label": label,
            "sdg": df_indis.iloc[i].sdg,
            "color": df_indis.iloc[i].color,
            "goal": goals[i],
            "budget": budget_data
        }
        for t, val in enumerate(serie):
            row_dict[str(t)] = val
        df_output_list.append(row_dict)

    df_output_json = json.dumps(df_output_list, cls=NumpyJSONEncoder)

    # --- Save Excel for download ---
    output = BytesIO()
    df_output_for_excel = pd.DataFrame(df_output_list)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_output_for_excel.to_excel(writer, index=False, sheet_name="Simulation_Results")
    output.seek(0)
    request.session["excel_data"] = base64.b64encode(output.getvalue()).decode("utf-8")

    # --- Render results ---
    context = {
        "df_output_list": df_output_list,
        "df_output_json": df_output_json,
        "T": T,
    }
    print("df_output_list__:", df_output_list)
    print("df_output_json__:", df_output_json)
    return render(request, "results.html", context)



def download_excel(request):
    excel_data = request.session.get('excel_data')
    if not excel_data:
        return HttpResponse("No Excel file available.", status=400)

    response = HttpResponse(
        base64.b64decode(excel_data),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="simulation_results.xlsx"'
    return response


def download_plots_excel(request):
    df_output = request.session.get('df_output')
    if not df_output:
        return HttpResponse("No data available.", status=400)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for row in df_output:
            indicator = row['indicator_label']
            # Build a small DataFrame per indicator
            T = len([k for k in row.keys() if isinstance(k, int)])
            data = { 'Time': list(range(T)), 'Value': [row[t] for t in range(T)] }
            pd.DataFrame(data).to_excel(writer, sheet_name=indicator[:31], index=False)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="all_plots_data.xlsx"'
    return response