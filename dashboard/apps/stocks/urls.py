"""
URLs para a API REST de dados de ações.

Este módulo define as rotas da API para acessar dados de ações,
indicadores técnicos e metadados.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StockDataViewSet, TechnicalIndicatorsViewSet, 
    DataMetadataViewSet, FilterOptionsViewSet
)

# Configuração do router
router = DefaultRouter()
router.register(r'stocks', StockDataViewSet, basename='stocks')
router.register(r'indicators', TechnicalIndicatorsViewSet, basename='indicators')
router.register(r'metadata', DataMetadataViewSet, basename='metadata')
router.register(r'filters', FilterOptionsViewSet, basename='filters')

urlpatterns = [
    path('', include(router.urls)),
] 