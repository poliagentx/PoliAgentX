from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
from django.conf import settings
from datetime import datetime
import uuid
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib import messages
from django.http import FileResponse, HttpResponse

from PoliagentX.backend_poliagentx.model_calibration import calibrate_model
from PoliagentX.backend_poliagentx.simple_prospective_simulation import run_simulation
from PoliagentX.backend_poliagentx.structural_bottlenecks import analyze_structural_bottlenecks
from .forms import BudgetForm
import io
from openpyxl import Workbook

from .forms import Uploaded_indicators,BudgetForm,Uploaded_Budget

from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .forms import Uploaded_indicators
from django.core.exceptions import ValidationError

import os
import tempfile
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages



def upload_indicators(request):
    if request.method == 'POST':
        form = Uploaded_indicators(request.POST, request.FILES)
        if form.is_valid():
            messages.success(request, "☑️ File validation successful!")
            return render(request, 'indicators.html', {
                'form': Uploaded_indicators(),  # reset form
            })

        # messages.error(request, " Please correct the highlighted errors below.")
        return render(request, 'indicators.html', {'form': form})

    
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

            # Adjusting for inflation
            adjusted_budget = budget / (1 + (inflation / 100))

            # Prepare SDG allocation rows: [program_ID, expenditure]
            expenditure_rows = [
                [i + 1, round(adjusted_budget * sdg["percent"] / 100, 2)]
                for i, sdg in enumerate(SDG_ALLOCATION)
            ]

            # Create Excel file
            wb = Workbook()
            ws = wb.active
            ws.title = "template_expenditure"

            # Header
            ws.append(["program_ID", "expenditure"])

            # Data rows
            for row in expenditure_rows:
                ws.append(row)

            # Create response
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=kenya_adjusted_budget.xlsx'

            # Save workbook to response
            with io.BytesIO() as buffer:
                wb.save(buffer)
                response.write(buffer.getvalue())

            return response
    else:
        form = BudgetForm()

    return render(request, 'your_app/budget_form.html', {'form': form})

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


