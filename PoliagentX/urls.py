from django.urls import *
from jupyter_core.version import pattern

from . import views

urlpatterns=[
    path('',views.example,name='example'),
    path("__reload__/", include("django_browser_reload.urls")),
]
