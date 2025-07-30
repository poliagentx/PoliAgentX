from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    
    # CompleteWorkflowView,
    # WorkflowStatusView,
    # DownloadResultView,
    # BottleneckAnalysisView,
    # ExcelToTableView,
    
    upload_expenditure,
    upload_indicators,
    download_indicator_template,
    download_budget_template,
    process_whole_budget,
    upload_network,
    download_network_template,
    calibration
)


urlpatterns = [
 
    path("__reload__/", include("django_browser_reload.urls")),
    path('download_indicator_template/', download_indicator_template, name='download_indicator_template'),
    path('upload-indicators/', upload_indicators, name='upload_indicators'),
    path('', lambda request: redirect('upload_indicators', permanent=False)),
    path('upload-expenditure/', upload_expenditure, name='upload_expenditure'),
    path('', lambda request: redirect('upload_expenditure', permanent=False)),
    path('download_budget_template/', download_budget_template, name='download_budget_template'),
    path('process_whole_budget/', process_whole_budget, name='process_whole_budget'),
    path('', lambda request: redirect('process_whole_budget', permanent=False)),
    path('download_network_template/', download_network_template, name='download_network_template'),
    path('upload-network/', upload_network, name='upload_network'),
    path('', lambda request: redirect('upload_network', permanent=False)),
    path('calibration/', calibration, name='calibration'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

