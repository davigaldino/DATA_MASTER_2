from django.urls import path
from . import views

urlpatterns = [
    path('', views.etl_demo_view, name='etl_demo'),
    path('upload/', views.upload_csv, name='etl_demo_upload'),
    path('status/<str:session_id>/', views.get_processing_status, name='etl_demo_status'),
    path('process/<str:session_id>/', views.process_csv, name='etl_demo_process'),
] 