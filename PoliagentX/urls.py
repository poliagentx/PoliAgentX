from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import (
    
    # CompleteWorkflowView,
    # WorkflowStatusView,
    # DownloadResultView,
    # BottleneckAnalysisView,
    # ExcelToTableView,
    upload_expenditure,
    upload_indicators,
    download_template,
    download_budget,
)

urlpatterns = [
 
    path("__reload__/", include("django_browser_reload.urls")),

    path('upload-indicators/', upload_indicators, name='upload_indicators'),
    path('', lambda request: redirect('upload_indicators', permanent=False)),
    path('download_template/', download_template, name='download_template'),
    path('download_template/', download_budget, name='download_budget'),
    path('upload-budget/', upload_expenditure, name='upload_expenditure'),
    path('', lambda request: redirect('upload_expenditure', permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
