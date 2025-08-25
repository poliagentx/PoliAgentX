import json
import base64
from io import BytesIO
import os
import random
import json
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

            # Try loading Excel data
            try:
                data = pd.read_excel(temp_file_path)
                data_filtered = data.drop(['monitoring', 'rule_of_law'], axis=1)
            except Exception as e:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "message": f"❌ Failed to read Excel file: {str(e)}"})
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
                    if request.headers.get("x-requested-with") == "XMLHttpRequest":
                        return JsonResponse({"success": False, "message": f"Error processing row {index}: {str(e)}"})
                    messages.error(request, f"Error processing row {index}: {str(e)}")
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
            # from django.conf import settings

            # debug_dir = os.path.join(settings.BASE_DIR, 'clean_data')
            # os.makedirs(debug_dir, exist_ok=True)

            # output_path = os.path.join(debug_dir, 'data_indicators.xlsx')
            # df.to_excel(output_path, index=False)
            # print(f"✅ Debug indicators file saved at: {output_path}")

            
            
            # Save to temporary cleaned Excel
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            tmp_file.close()
            with pd.ExcelWriter(tmp_file.name) as writer:
                df.to_excel(writer, sheet_name='template', index=False)

            request.session['indicators_path'] = tmp_file.name

            # If AJAX → return JSON
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "message": "Validation successful",
                    "stats": {
                        "total_indicators": len(df)
                    }
                })

            # If normal form POST → Django messages
            messages.success(request, "Validation successful")
            return render(request, 'indicators.html', {'form': Uploaded_indicators()})

        # Invalid form
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "message": "Invalid form submission"})
        return render(request, 'indicators.html', {'form': form})

    # GET request
    return render(request, 'indicators.html', {'form': Uploaded_indicators()})


def budgets_page(request):
    # Ensure indicators file exists in session
    indicators_path = request.session.get('indicators_path')
    if not indicators_path:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "message": "Indicators file is missing."})
        messages.error(request, "Indicators file is missing. Please upload it first.")
        return redirect('upload_indicators')

    allocation = get_sdg_allocation_from_file(indicators_path)
    budget_form = BudgetForm()
    upload_form = Uploaded_Budget()
    data_exp = None

    if request.method == 'POST':
        data_indi = pd.read_excel(indicators_path)

        # ---------------- File Upload ----------------
        if 'government_expenditure' in request.FILES:
            upload_form = Uploaded_Budget(request.POST, request.FILES)
            if not upload_form.is_valid():
                return JsonResponse({"success": False, "message": "Invalid file upload."})
            try:
                uploaded_file = request.FILES['government_expenditure']
                data_exp = pd.read_excel(BytesIO(uploaded_file.read()))
                if 'sdg' not in data_exp.columns:
                    return JsonResponse({"success": False, "message": "Uploaded file must have an 'sdg' column."})

                # Filter for matching & instrumental SDGs
                data_exp = data_exp[data_exp.sdg.isin(data_indi.sdg.values)]
                data_exp = data_exp[data_exp.sdg.isin(data_indi[data_indi.instrumental == 1].sdg.values)]

            except Exception as e:
                return JsonResponse({"success": False, "message": f"Failed to read uploaded file: {e}"})

            # Add Django success message
            # messages.success(request, "Budget data uploaded successfully!")

        # ---------------- Manual Input ----------------
        elif 'budget' in request.POST:
            budget_form = BudgetForm(request.POST)
            if not budget_form.is_valid():
                return JsonResponse({"success": False, "message": "Invalid manual budget input."})

            budget = budget_form.cleaned_data['budget']
            inflation = budget_form.cleaned_data['inflation_rate']
            adjusted_budget = budget / (1 + (inflation / 100))

            years = sorted([int(col) for col in data_indi.columns if str(col).isdigit()])
            periods = len(years)

            data_exp = pd.DataFrame([
                {
                    'sdg': i + 1,
                    **{str(years[0] + j): round(adjusted_budget * sdg['percent'] / 100 / periods, 2)
                       for j in range(periods)}
                }
                for i, sdg in enumerate(allocation)
            ])

            data_exp = data_exp[data_exp.sdg.isin(data_indi.sdg.values)]
            data_exp = data_exp[data_exp.sdg.isin(data_indi[data_indi.instrumental == 1].sdg.values)]

            # Add Django success message
            # messages.success(request, "Manual budget submitted successfully!")

        else:
            return JsonResponse({"success": False, "message": "No input provided."})

        # ---------------- Process & Save ----------------
        df_exp = expand_budget(data_exp)
        df_rel = build_relational_table(data_indi)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            with pd.ExcelWriter(tmp_file.name) as writer:
                df_exp.to_excel(writer, sheet_name='template_budget', index=False)
                df_rel.to_excel(writer, sheet_name='relational_table', index=False)

            request.session['budget_file_path'] = tmp_file.name
                 # Save to cleaned Excel
            # from django.conf import settings

            # debug_dir = os.path.join(settings.BASE_DIR, 'clean_data')
            # os.makedirs(debug_dir, exist_ok=True)

            # output_path = os.path.join(debug_dir, 'exp.xlsx')
            # df_exp.to_excel(output_path, index=False)
            # print(f" Debug indicators file saved at: {output_path}")

        return JsonResponse({"success": True, "message": " Validation successful!"})

    # ---------------- GET Request ----------------
    return render(request, 'budgets.html', {
        'budget_form': budget_form,
        'upload_form': upload_form,
    })



def upload_network(request):
    indicators_path = request.session.get('indicators_path')
    if not indicators_path:
        messages.error(request, "Indicators file is missing. Please upload it first.")
        return redirect('upload_indicators')

    if request.method == 'POST':
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        data_net = None

        # -----------------------------
        # Case 1: User uploaded a file
        # -----------------------------
        if 'interdependency_network' in request.FILES:
            uploaded_form = Uploaded_networks(request.POST, request.FILES)
            if uploaded_form.is_valid():
                uploaded_file = request.FILES['interdependency_network']
                try:
                    data_net = pd.read_excel(BytesIO(uploaded_file.read()))
                except Exception as e:
                    error_message = f"Failed to read uploaded file: {e}"
                    if is_ajax:
                        return JsonResponse({'success': False, 'message': error_message})
                    messages.error(request, error_message)
                    return redirect('upload_network')

        # -----------------------------
        # Case 2: User skipped upload
        # -----------------------------
        elif 'skip-network' in request.POST:
            skip_form = Skip_networks(request.POST)
            if skip_form.is_valid():
                try:
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
                except Exception as e:
                    error_message = f"Failed to generate default network: {e}"
                    if is_ajax:
                        return JsonResponse({'success': False, 'message': error_message})
                    messages.error(request, error_message)
                    return redirect('upload_network')

        # -----------------------------
        # Save the dataframe
        # -----------------------------
        if data_net is not None:
            try:
                wb = Workbook()
                ws_network = wb.active
                ws_network.title = "template_network"
                for r in dataframe_to_rows(data_net, index=False, header=True):
                    ws_network.append(r)

                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    wb.save(tmp_file.name)
                    request.session['network_path'] = tmp_file.name
                    
                    # os.makedirs('clean_data', exist_ok=True)
                    # output_path = os.path.join('clean_data', 'network.xlsx')    
                    # data_net.to_excel(output_path, index=False)

                success_message = "Validation successful."

                if is_ajax:
                    return JsonResponse({'success': True, 'message': success_message})
                else:
                    messages.success(request, success_message)

                    if 'skip-network' in request.POST:
                        return redirect('calibration')  # Skip → move forward
                    return redirect('upload_network')  # Upload → stay

            except Exception as e:
                error_message = f"Failed to save network: {e}"
                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_message})
                messages.error(request, error_message)
                return redirect('upload_network')
        # return JsonResponse({"success": True, "message": "Validation successful!"})
    # -----------------------------
    # Default GET request
    # -----------------------------
    skip_form = Skip_networks()
    uploaded_form = Uploaded_networks()
    return render(request, 'Network.html', {
        'skip_form': skip_form,
        'uploaded_form': uploaded_form
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
            # Get threshold safely
            try:
                threshold = float(request.POST.get('threshold', 0.5))
            except (ValueError, TypeError):
                threshold = 0.5

            # Run calibration (your function)
            parameters = run_calibration(request, threshold=threshold)
            parameters = pd.DataFrame(parameters)

            # Save calibration output
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            tmp_file.close()
            with pd.ExcelWriter(tmp_file.name) as writer:
                parameters.to_excel(writer, sheet_name='template', index=False)

            # Save path + calibration flag in session
            request.session['param_excel_path'] = tmp_file.name
            request.session['calibrated'] = True
            # ✅ flag that calibration is done
            # from django.conf import settings
            # debug_dir = os.path.join(settings.BASE_DIR, 'clean_data')
            # os.makedirs(debug_dir, exist_ok=True)

            # output_path = os.path.join(debug_dir, 'para.xlsx')
            # parameters.to_excel(output_path, index=False)
            
            # print(f"✅ Debug  file saved at: {output_path}")
            # print("POST data:", request.POST.dict())
            
            return render(request, 'calibration.html', {
                'threshold': threshold,
                'parameters': parameters,
            })

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)



# A custom JSONEncoder class to handle NumPy data types
class NumpyJSONEncoder(json.JSONEncoder):
    """
    A custom JSON encoder that handles NumPy data types and pandas objects.
    This prevents 'TypeError: Object of type int64 is not JSON serializable'
    by converting NumPy integers, floats, and arrays to standard Python types.
    """
    def default(self, obj):
        # Handle NumPy integer types (including int64, int32, etc.)
        if isinstance(obj, np.integer):
            return int(obj)
        # Handle NumPy floating-point types (including float64, float32, etc.)
        elif isinstance(obj, np.floating):
            # Handle NaN values
            if np.isnan(obj):
                return None
            return float(obj)
        # Handle NumPy arrays
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        # Handle pandas Series
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        # Handle pandas Timestamp
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        # Handle pandas NaT (Not a Time)
        elif pd.isna(obj):
            return None
        # Handle numpy bool types
        elif isinstance(obj, np.bool_):
            return bool(obj)
        # Fallback: try to convert to standard Python types
        elif hasattr(obj, 'item'):  # NumPy scalars have .item() method
            return obj.item()
        # Additional debug info - comment out in production
        else:
            print(f"DEBUG: Unhandled type in JSON encoder: {type(obj)} - {obj}")
            # Try to convert to string as last resort
            try:
                return str(obj)
            except:
                pass
        
        # Fallback to the base class's default method for all other types.
        return super().default(obj)
def results(request):
    if request.method == "POST":
        # Get required file paths from session
        param_excel_path = request.session.get('param_excel_path')
        network_path = request.session.get('network_path')
        budget_path = request.session.get('budget_file_path')
        indicators_path = request.session.get('indicators_path')

        # Validate that all required files are present
        if not all([param_excel_path, network_path, budget_path, indicators_path]):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Missing required files.'}, status=400)
            return HttpResponse("Missing required files.", status=400)

        try:
            # Load indicators data
            df_indis = pd.read_excel(indicators_path)
            N = len(df_indis)
            I0 = df_indis.I0.values
            R = df_indis.instrumental
            qm = df_indis.qm.values
            rl = df_indis.rl.values
            indis_index = {code: i for i, code in enumerate(df_indis.indicator_label)}
            Imax = df_indis.max_value.values
            Imin = df_indis.min_value.values

            # Load parameters data
            df_params = pd.read_excel(param_excel_path, skiprows=1)
            alpha = df_params.alpha.values
            alpha_prime = df_params.alpha_prime.values
            betas = df_params.beta.values

            # Load network data
            df_net = pd.read_excel(network_path)
            A = np.zeros((N, N))
            for _, row in df_net.iterrows():
                i = indis_index[row.origin]
                j = indis_index[row.destination]
                A[i, j] = row.weight

            # Get number of simulation periods from form
            T = int(request.POST.get("num_simulations", 50))

            # Load budget data
            df_exp = pd.read_excel(budget_path, sheet_name='template_budget')
            Bs_retrospective = df_exp.values[:, 1:]
            Bs = np.tile(Bs_retrospective[:, -1], (T, 1)).T

            # Load relational table
            df_rela = pd.read_excel(budget_path, sheet_name='relational_table')
            B_dict = {
                indis_index[row.indicator_label]: [p for p in row.values[1:] if pd.notna(p)]
                for _, row in df_rela.iterrows()
            }

            # Generate random goals
            goals = np.random.rand(N) * (Imax - I0) + I0

            # Run simulation
            sample_size = 100
            outputs = []
            for _ in range(sample_size):
                output = run_ppi(I0, alpha, alpha_prime, betas, A=A, Bs=Bs, B_dict=B_dict, 
                               T=T, R=R, qm=qm, rl=rl, Imax=Imax, Imin=Imin, G=goals)
                outputs.append(output)

            # Process simulation results
            tsI, tsC, tsF, tsP, tsS, tsG = zip(*outputs)
            tsI_hat = np.mean(tsI, axis=0)

            # Build the list of dictionaries for output
            df_output_list = []
            for i, serie in enumerate(tsI_hat):
                # Get the row data and convert types explicitly
                indicator_row = df_indis.iloc[i]
                
                row_dict = {
                    'indicator_label': str(indicator_row.indicator_label),
                    'sdg': int(indicator_row.sdg) if pd.notna(indicator_row.sdg) else None,
                    'color': str(indicator_row.color),
                    'goal': float(goals[i])
                }
                
                # Add time series data, ensuring all values are floats
                for t, val in enumerate(serie):
                    # Handle potential NaN or inf values
                    if pd.isna(val) or np.isinf(val):
                        row_dict[str(t)] = None
                    else:
                        row_dict[str(t)] = float(val)
                
                df_output_list.append(row_dict)
            
            # Debug: Check data types before JSON serialization
            # Uncomment the next few lines if you need to debug data types
            # print("DEBUG: Sample data types in first row:")
            # if df_output_list:
            #     for key, value in df_output_list[0].items():
            #         print(f"  {key}: {type(value)} = {value}")
                
            # Serialize data to JSON with custom encoder
            try:
                df_output_json = json.dumps(df_output_list, cls=NumpyJSONEncoder)
            except TypeError as e:
                print(f"JSON serialization error: {e}")
                # If custom encoder fails, try with explicit conversion
                df_output_json = json.dumps(df_output_list, default=str)

            # Generate Excel file for download
            output = BytesIO()
            df_output_for_excel = pd.DataFrame(df_output_list)
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_output_for_excel.to_excel(writer, index=False, sheet_name="Simulation_Results")
            output.seek(0)
            request.session['excel_data'] = base64.b64encode(output.getvalue()).decode('utf-8')

            # Store simulation results in session for later use
            request.session['simulation_results'] = {
                'df_output_list': df_output_list,
                'df_output_json': df_output_json,
                'T': T,
            }

            # Handle AJAX request (from the new template)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Simulation completed successfully',
                    'periods': T,
                    'indicators_count': N,
                })
            
            # Handle regular form submission (fallback or direct access)
            context = {
                'df_output_list': df_output_list,
                'df_output_json': df_output_json,
                'T': T,
            }
            return render(request, "results.html", context)
            
        except Exception as e:
            # Handle any errors that occur during simulation
            error_message = f"Simulation failed: {str(e)}"
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': error_message}, status=500)
            return HttpResponse(error_message, status=500)
    
    # Handle GET requests - show results if they exist in session
    elif request.method == "GET":
        simulation_results = request.session.get('simulation_results')
        
        if simulation_results:
            context = {
                'df_output_list': simulation_results['df_output_list'],
                'df_output_json': simulation_results['df_output_json'],
                'T': simulation_results['T'],
            }
            return render(request, "results.html", context)
        else:
            # No simulation results available, redirect to simulation page
            return redirect('simulation')
    
    # Handle other HTTP methods
    return HttpResponse("Invalid request method.", status=405)

def download_excel(request):
    excel_data = request.session.get('excel_data')
    if not excel_data:
        return HttpResponse("No Excel file available.", status=400)

    response = HttpResponse(
        excel_data,
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




