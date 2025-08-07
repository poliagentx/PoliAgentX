from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    budgets_page,
    upload_indicators,
    download_indicator_template,
    download_budget_template,
    upload_network,
    download_network_template,
    calibration,
    simulation
)


urlpatterns = [
 
    path("__reload__/", include("django_browser_reload.urls")),
    path('download_indicator_template/', download_indicator_template, name='download_indicator_template'),
    path('upload-indicators/', upload_indicators, name='upload_indicators'),
    path('', lambda request: redirect('upload_indicators', permanent=False)),
    path('download_budget_template/', download_budget_template, name='download_budget_template'),
    path('upload-budgets/', budgets_page, name='budgets_page'),
    path('download_network_template/', download_network_template, name='download_network_template'),
    path('upload-network/', upload_network, name='upload_network'),
    path('calibration/',calibration,name='calibration'),
    path('simulation/', simulation, name='simulation'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)