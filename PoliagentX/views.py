import tempfile
import io
import os
from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from PoliagentX.backend_poliagentx.model_calibration import calibrate_model
from PoliagentX.backend_poliagentx.simple_prospective_simulation import run_simulation
from PoliagentX.backend_poliagentx.structural_bottlenecks import analyze_structural_bottlenecks
from openpyxl import Workbook
from .forms import Uploaded_indicators,BudgetForm,Uploaded_Budget, Uploaded_networks
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.staticfiles import finders
import pandas as pd
import numpy as np




def upload_indicators(request):
    if request.method == 'POST':
        form = Uploaded_indicators(request.POST, request.FILES)
        if form.is_valid():
            # Handle uploaded file
            uploaded_file = request.FILES['government_indicators']

            # Save file to a temporary location on disk
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)
                temp_file_path = tmp.name

            # Store path in session
            request.session['temp_excel_path'] = temp_file_path

            # Optional: show success message
            messages.success(request, "☑️ File validation successful!")

            # Reset the form for new upload
            return render(request, 'indicators.html', {
                'form': Uploaded_indicators()
            })

        # Form is invalid: show errors
        # messages.error(request, "Please correct the highlighted errors below.")
        return render(request, 'indicators.html', {'form': form})

    # GET request
    return render(request, 'indicators.html', {'form': Uploaded_indicators()})

# def upload_expenditure(request):
#     if request.method == 'POST':
#         form_exp = Uploaded_Budget(request.POST, request.FILES)
#         if form_exp.is_valid():
#             # Handle uploaded file
#             uploaded_file = request.FILES['government_expenditure']

#             # Save to a temporary file on disk
#             with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
#                 for chunk in uploaded_file.chunks():
#                     tmp.write(chunk)
#                 temp_file_path = tmp.name

#             # Store the temp file path in the session
#             request.session['temp_budget_path'] = temp_file_path

#             # Show success message and reset form
#             messages.success(request, "☑️ File validation successful!")
#             return render(request, 'budgets.html', {
#                 'form': Uploaded_Budget(),  # reset form
#             })

#         # If form is invalid
#         return render(request, 'budgets.html', {'form': form_exp})

#     # GET request
#     return render(request, 'budgets.html', {'form': Uploaded_Budget()})



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
    
SDG_ALLOCATION = [
    {"goal": "No Poverty", "percent": 10},
    {"goal": "Zero Hunger", "percent": 8},
    {"goal": "Good Health and Well-being", "percent": 12},
    {"goal": "Quality Education", "percent": 10},
    {"goal": "Gender Equality", "percent": 5},
    {"goal": "Clean Water and Sanitation", "percent": 6},
    {"goal": "Affordable and Clean Energy", "percent": 6},
    {"goal": "Decent Work and Economic Growth", "percent": 7},
    {"goal": "Industry, Innovation, and Infrastructure", "percent": 5},
    {"goal": "Reduced Inequality", "percent": 4},
    {"goal": "Sustainable Cities and Communities", "percent": 5},
    {"goal": "Responsible Consumption and Production", "percent": 3},
    {"goal": "Climate Action", "percent": 3},
    {"goal": "Life Below Water", "percent": 2},
    {"goal": "Life on Land", "percent": 2},
    {"goal": "Peace, Justice, and Strong Institutions", "percent": 6},
    {"goal": "Partnerships for the Goals", "percent": 6},
]

def budgets_page(request):
    budget_form = BudgetForm()
    upload_form = Uploaded_Budget()

    if request.method == 'POST':
        if 'process_budget' in request.POST:
            budget_form = BudgetForm(request.POST)
            if budget_form.is_valid():
                budget = budget_form.cleaned_data['budget']
                inflation = budget_form.cleaned_data['inflation_rate']
                adjusted_budget = budget / (1 + (inflation / 100))

                wb = Workbook()
                ws1 = wb.active
                ws1.title = "template_expenditure"
                ws1.append(["program_ID", "expenditure"])
                for i, sdg in enumerate(SDG_ALLOCATION):
                    amount = round(adjusted_budget * sdg["percent"] / 100, 2)
                    ws1.append([i + 1, amount])

                ws2 = wb.create_sheet(title="relational_table")
                ws2.append(["program_ID", "program_name", "goal"])
                for i, sdg in enumerate(SDG_ALLOCATION):
                    ws2.append([i + 1, f"Program {i + 1}", sdg["goal"]])

                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                    wb.save(tmp.name)
                    request.session['temp_excel_path'] = tmp.name

                messages.success(request, "☑️ Budget processed successfully with two sheets.")
                return redirect('upload_network')

        elif 'upload_budget' in request.POST:
            upload_form = Uploaded_Budget(request.POST, request.FILES)
            if upload_form.is_valid():
                uploaded_file = request.FILES['government_expenditure']
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                    for chunk in uploaded_file.chunks():
                        tmp.write(chunk)
                    request.session['temp_budget_path'] = tmp.name

                messages.success(request, "☑️ File validation successful!")
                return redirect('upload_network')  # or re-render same page

    return render(request, 'budgets.html', {
        'budget_form': budget_form,
        'upload_form': upload_form,
    })

# def process_whole_budget(request):
#     if request.method == 'POST':
#         form_whole = BudgetForm(request.POST)
#         if form_whole.is_valid():
#             budget = form_whole.cleaned_data['budget']
#             inflation = form_whole.cleaned_data['inflation_rate']

#             # Adjust for inflation
#             adjusted_budget = budget / (1 + (inflation / 100))

#             # Create workbook with two sheets
#             wb = Workbook()

#             # Sheet 1: Expenditure
#             ws1 = wb.active
#             ws1.title = "template_expenditure"
#             ws1.append(["program_ID", "expenditure"])
#             for i, sdg in enumerate(SDG_ALLOCATION):
#                 amount = round(adjusted_budget * sdg["percent"] / 100, 2)
#                 ws1.append([i + 1, amount])

#             # Sheet 2: Relational Table
#             ws2 = wb.create_sheet(title="relational_table")
#             ws2.append(["program_ID", "program_name", "goal"])
#             for i, sdg in enumerate(SDG_ALLOCATION):
#                 ws2.append([i + 1, f"Program {i + 1}", sdg["goal"]])

#             # Save to a single temporary file
#             with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
#                 wb.save(tmp.name)
#                 request.session['temp_excel_path'] = tmp.name

#             messages.success(request, "☑️ Budget processed successfully with two sheets.")
#             return redirect('upload_network')  
#     else:
#         form = BudgetForm()

#     return render(request, 'budgets.html', {'form': form})


def upload_network(request):
    if request.method == 'POST':
        temp_file_path = request.session.get('temp_excel_path')  # Make sure this key matches upload_indicators()

        if not temp_file_path or not os.path.exists(temp_file_path):
            return HttpResponse("File not found.", status=404)

        form = Uploaded_networks(request.POST, request.FILES)
        if form.is_valid():
            # Load Excel data
            try:
                data = pd.read_excel(temp_file_path)
            except Exception as e:
                return HttpResponse(f"Failed to read Excel file: {e}", status=400)

            # Begin matrix processing
            N = len(data)
            M = np.zeros((N, N))

            # Find year columns
            years = [col for col in data.columns if str(col).isnumeric()]

            for i, rowi in data.iterrows():
                for j, rowj in data.iterrows():
                    if i != j:
                        serie1 = rowi[years].values.astype(float)[1:]
                        serie2 = rowj[years].values.astype(float)[:-1]

                        change_serie1 = serie1[1:] - serie1[:-1]
                        change_serie2 = serie2[1:] - serie2[:-1]

                        if not np.all(change_serie1 == change_serie1[0]) and not np.all(change_serie2 == change_serie2[0]):
                            corr = np.corrcoef(change_serie1, change_serie2)[0, 1]
                            if not np.isnan(corr):
                                M[i, j] = corr

            M[np.abs(M) < 0.5] = 0

            # Build edge list
            ids = data['seriesCode'].values
            edge_list = []
            for i, j in zip(*np.where(M != 0)):
                edge_list.append([ids[i], ids[j], M[i, j]])

            # Save result to CSV
            df = pd.DataFrame(edge_list, columns=['origin', 'destination', 'weight'])
            os.makedirs('clean_data', exist_ok=True)
            df.to_excel('clean_data/data_network.xlsx', index=False)

            # Success feedback
            messages.success(request, "☑️ File processed and network created.")
            return render(request, 'Network.html', {
                'form': Uploaded_networks()  # Reset form
            })

        # Form invalid
        return render(request, 'Network.html', {'form': form})

    # GET request
    return render(request, 'Network.html', {'form': Uploaded_networks()})
   
def calibration(request):
    return render(request,'calibration.html')
def simulation(request):
    return render(request,'simulation.html')