import uuid
from django.db import models


class DAGRun(models.Model):
    STATUS_CHOICES = [
        ("QUEUED", "Em Fila"),
        ("RUNNING", "Executando"),
        ("SUCCESS", "Sucesso"),
        ("FAILED", "Falha"),
    ]

    run_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    dag_name = models.CharField(max_length=255)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="QUEUED")
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    failed_tasks = models.IntegerField(default=0)
    log_output = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.dag_name} - {self.run_id} ({self.status})"

    class Meta:
        verbose_name = "DAG Run"
        verbose_name_plural = "DAG Runs"


class TaskInstance(models.Model):
    STATUS_CHOICES = [
        ("QUEUED", "Em Fila"),
        ("RUNNING", "Executando"),
        ("SUCCESS", "Sucesso"),
        ("FAILED", "Falha"),
    ]

    dag_run = models.ForeignKey(DAGRun, on_delete=models.CASCADE, related_name="task_instances")
    task_id = models.CharField(max_length=255)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="QUEUED")
    log_output = models.TextField(blank=True, null=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.dag_run.dag_name}.{self.task_id} ({self.status})"

    class Meta:
        verbose_name = "Task Instance"
        verbose_name_plural = "Task Instances" 