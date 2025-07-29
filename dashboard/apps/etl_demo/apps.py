from django.apps import AppConfig

class EtlDemoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.etl_demo'
    verbose_name = 'ETL Demo' 