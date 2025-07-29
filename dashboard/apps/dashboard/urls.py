"""
URLs para o dashboard Django.

Este módulo define as rotas para o dashboard principal
e integração com a aplicação Dash.
"""

from django.urls import path
from . import views, etl_views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('api/', views.dashboard_api, name='dashboard_api'),
    path('etl/', etl_views.etl_dashboard, name='etl_dashboard'),
    path('etl/start/', etl_views.start_etl, name='start_etl'),
    path('etl/progress/', etl_views.get_etl_progress, name='get_etl_progress'),
    path('etl/clear/', etl_views.clear_database, name='clear_database'),
    path('etl/db-status/', etl_views.get_database_status, name='get_database_status'),
] 