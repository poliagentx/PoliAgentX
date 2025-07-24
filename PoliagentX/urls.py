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
)


urlpatterns = [
 
    path("__reload__/", include("django_browser_reload.urls")),

    path('upload-indicators/', upload_indicators, name='upload_indicators'),
    path('', lambda request: redirect('upload_indicators', permanent=False)),
    path('download_indicator_template/', download_indicator_template, name='download_indicator_template'),
    path('download_budget_template/', download_budget_template, name='download_budget_template'),
    path('process_whole_budget/', process_whole_budget, name='process_whole_budget'),
    path('upload-expenditure/', upload_expenditure, name='upload_expenditure'),
    path('', lambda request: redirect('upload_expenditure', permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
