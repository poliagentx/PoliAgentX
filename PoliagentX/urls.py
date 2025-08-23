from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from .views import*

urlpatterns = [
 
    path("__reload__/", include("django_browser_reload.urls")),
    path('upload-indicators/', upload_indicators, name='upload_indicators'),
    path('', lambda request: redirect('upload_indicators', permanent=False)),
    path('download_indicator_template/', download_indicator_template, name='download_indicator_template'),
    path('download_budget_template/', download_budget_template, name='download_budget_template'),
    path('', lambda request: redirect('upload_expenditure', permanent=False)),
    path('upload_network/', upload_network, name='upload_network'),
    path('download_network_template/', download_network_template, name='download_network_template'),
    path('budgets/', budgets_page, name='budgets_page'),
    path('calibration/',calibration,name='calibration'),
    path('simulation/', simulation, name='simulation'),
    path('start_calibration/', start_calibration, name='start_calibration'),
    path('results/', results, name="results"),
    path('download_excel/', download_excel, name='download_excel'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)