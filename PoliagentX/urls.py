from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from .views import*

urlpatterns = [
 
    path("__reload__/", include("django_browser_reload.urls")),
    path('download_indicator_template/', download_indicator_template, name='download_indicator_template'),
    path('upload-indicators/', upload_indicators, name='upload_indicators'),
    path('', lambda request: redirect('upload_indicators', permanent=False)),
    path('download_budget_template/', download_budget_template, name='download_budget_template'),
    # path('process_whole_budget/', process_whole_budget, name='process_whole_budget'),
    # path('upload-expenditure/', upload_expenditure, name='upload_expenditure'),
    path('upload_network/', upload_network, name='upload_network'),
    path('download_network_template/', download_network_template, name='download_network_template'),
    path('budgets/', budgets_page, name='budgets_page'),
    path('calibration/', calibration, name='calibration'),
    path('start_calibration/', start_calibration, name='start_calibration'),
    path('run_simulation/', run_simulation, name='run_simulation'),
    path('simulation/', simulation, name='simulation'),
    path('results/', results, name='results'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)