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


def upload_indicators(request):
    if request.method == 'POST':
        form = Uploaded_indicators(request.POST, request.FILES)
        if form.is_valid():
            # Handle uploaded file
            uploaded_file = form.cleaned_data['government_indicators']

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

def upload_expenditure(request):
    if request.method == 'POST':
        form = Uploaded_Budget(request.POST, request.FILES)
        if form.is_valid():
            messages.success(request, "☑️ File validation successful!")
            return render(request, 'budgets.html', {
                'form': Uploaded_Budget(),  # reset form
            })

        # messages.error(request, " Please correct the highlighted errors below.")
        return render(request, 'budgets.html', {'form': form})



    return render(request, 'budgets.html', {'form': Uploaded_Budget()})




from django.contrib.staticfiles import finders

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

def process_whole_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.cleaned_data['budget']
            inflation = form.cleaned_data['inflation_rate']

            # Adjust for inflation
            adjusted_budget = budget / (1 + (inflation / 100))

            # Prepare SDG allocation rows
            expenditure_rows = [
                [i + 1, round(adjusted_budget * sdg["percent"] / 100, 2)]
                for i, sdg in enumerate(SDG_ALLOCATION)
            ]

            # Create Excel workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "template_expenditure"
            ws.append(["program_ID", "expenditure"])
            for row in expenditure_rows:
                ws.append(row)

            # Save to a temporary file on disk
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                wb.save(tmp.name)
                temp_file_path = tmp.name

            # Store the temp file path in the session
            request.session['temp_excel_path'] = temp_file_path

            # Redirect to display the file (or whatever processing is next)
            return redirect('Network.html')  # Make sure to define this view and URL
    else:
        form = BudgetForm()

    return render(request, 'budgets.html', {'form': form})


def download_budget_template(request):
    filepath = finders.find('templates/template_network.xlsx')
    if filepath and os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='template_network.xlsx')
    else:
        return HttpResponse("Template file not found.", status=404)
    

def upload_network(request):
    if request.method == 'POST':
        form = Uploaded_networks(request.POST, request.FILES)
        if form.is_valid():
            messages.success(request, "☑️ File validation successful!")
            return render(request, 'Network.html', {
                'form': Uploaded_networks(),  # reset form
            })

        # messages.error(request, " Please correct the highlighted errors below.")
        return render(request, 'Network.html', {'form': form})

    return render(request, 'Network.html', {'form': Uploaded_indicators()})


# def process_expenditure_template(request):
#     if request.method == 'POST':
#         form = Uploaded_Budget(request.POST, request.FILES)
#         if form.is_valid():
#             messages.success(request, "☑️ File validation successful!")
#             return render(request, 'expenditure.html', {
#                 'form': Uploaded_Budget(),  # reset form
#             })

#         # messages.error(request, " Please correct the highlighted errors below.")
#         return render(request, 'expenditure.html', {'form': form})

#     return render(request, 'expenditure.html', {'form': Uploaded_Budget()})


