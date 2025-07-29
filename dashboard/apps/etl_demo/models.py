from django.db import models
import uuid
import json

class ETLSession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=[
        ('uploaded', 'Uploaded'),
        ('validating', 'Validating'),
        ('cleaning', 'Cleaning'),
        ('transforming', 'Transforming'),
        ('loading', 'Loading'),
        ('completed', 'Completed'),
        ('error', 'Error')
    ], default='uploaded')
    current_step = models.CharField(max_length=50, blank=True)
    progress = models.IntegerField(default=0)
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    cleaned_rows = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)  # Para estatísticas detalhadas
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.filename} - {self.status}"

class ETLLog(models.Model):
    session = models.ForeignKey(ETLSession, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10, choices=[
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error')
    ])
    message = models.TextField()
    step = models.CharField(max_length=50)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.level}] {self.message}" 