from django.urls import path, include
from . import views
from .views import (
    
    CompleteWorkflowView,
    WorkflowStatusView,
    DownloadResultView,
    BottleneckAnalysisView
)

urlpatterns = [
    # path('', views.example, name='example'),

    # For Django browser reload (live reloading during development)
    path("__reload__/", include("django_browser_reload.urls")),

    # # API endpoints
    # path('api/prepare-expenditure/', ExpenditurePreparationView.as_view(), name='prepare-expenditure'),
    # path('api/prepare-indicators/', IndicatorPreparationView.as_view(), name='prepare-indicators'),
    # path('api/prepare-interdependencies/', InterdependenciesPreparationView.as_view(), name='prepare-interdependencies'),
    # path('api/calibrate-model/', ModelCalibrationView.as_view(), name='calibrate-model'),
    # path('api/run-simulation/', SimulationView.as_view(), name='run-simulation'),
    
    path('api/complete-workflow/', CompleteWorkflowView.as_view(), name='complete-workflow'),
    path('api/workflow-status/<str:run_id>/', WorkflowStatusView.as_view(), name='workflow-status'),
    path('api/download/<str:run_id>/<str:file_type>/', DownloadResultView.as_view(), name='download-result'),
    path('api/bottleneck-analysis/', BottleneckAnalysisView.as_view(), name='bottleneck-analysis'),
]
