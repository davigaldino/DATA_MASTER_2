"""
URLs para demonstração do Airflow
"""

from django.urls import path
from . import views

app_name = 'airflow_demo'

urlpatterns = [
    path('', views.airflow_demo_view, name='index'),
    path('start/', views.start_dag, name='start_dag'),
    path('status/<uuid:dag_run_id>/', views.get_dag_status, name='get_dag_status'),
    path('status/latest/', views.get_latest_dag_run, name='get_latest_dag_run'),
    path('clear/', views.clear_dag_history, name='clear_dag_history'),
] 