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



from .forms import Uploaded_indicators,Uploaded_expenditure,Uploaded_interdepenency

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
from .forms import Uploaded_indicators


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
        form = Uploaded_indicators(request.POST, request.FILES)
        if form.is_valid():
            messages.success(request, "☑️ File validation successful!")
            return render(request, 'expenditure.html', {
                'form': Uploaded_expenditure(),  # reset form
            })

        # messages.error(request, " Please correct the highlighted errors below.")
        return render(request, 'expenditure.html', {'form': form})

    
    return render(request, 'expenditure.html', {'form': Uploaded_expenditure()})




from django.contrib.staticfiles import finders

def download_template(request):
    filepath = finders.find('templates/template_indicators.xlsx')
    if filepath and os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='template_indicators.xlsx')
    else:
        return HttpResponse("Template file not found.", status=404)

def download_budget(request):
    filepath = finders.find('templates/template_budget.xlsx')
    if filepath and os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='template_budget.xlsx')
    else:
        return HttpResponse("Template file not found.", status=404)




