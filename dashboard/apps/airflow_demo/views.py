"""
Views para demonstração do Airflow
"""

import json
import threading
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import DAGRun, TaskInstance
from .dag_simulator import run_dag_async


def airflow_demo_view(request):
    """View principal para demonstração do Airflow"""
    return render(request, 'airflow_demo/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def start_dag(request):
    """Inicia uma nova execução do DAG"""
    try:
        # Criar novo DAG Run
        dag_run = DAGRun.objects.create(
            dag_name="b3_data_pipeline_demo",
            status="QUEUED"
        )
        
        # Iniciar execução em thread separada
        thread = threading.Thread(
            target=run_dag_async,
            args=(dag_run.run_id,)
        )
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True,
            'message': 'DAG iniciado com sucesso',
            'dag_run_id': str(dag_run.run_id)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao iniciar DAG: {str(e)}'
        }, status=500)


def get_dag_status(request, dag_run_id):
    """Retorna o status atual do DAG Run"""
    try:
        dag_run = DAGRun.objects.get(run_id=dag_run_id)
        
        # Obter tarefas
        task_instances = dag_run.task_instances.all()
        tasks_data = []
        
        for task in task_instances:
            tasks_data.append({
                'task_id': task.task_id,
                'status': task.status,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'duration_seconds': task.duration_seconds,
                'log_output': task.log_output
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'dag_run_id': str(dag_run.run_id),
                'dag_name': dag_run.dag_name,
                'status': dag_run.status,
                'start_time': dag_run.start_time.isoformat(),
                'end_time': dag_run.end_time.isoformat() if dag_run.end_time else None,
                'total_tasks': dag_run.total_tasks,
                'completed_tasks': dag_run.completed_tasks,
                'failed_tasks': dag_run.failed_tasks,
                'log_output': dag_run.log_output,
                'tasks': tasks_data
            }
        })
        
    except DAGRun.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'DAG Run não encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao obter status: {str(e)}'
        }, status=500)


def get_latest_dag_run(request):
    """Retorna o DAG Run mais recente"""
    try:
        latest_run = DAGRun.objects.order_by('-start_time').first()
        
        if not latest_run:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum DAG Run encontrado'
            }, status=404)
        
        return get_dag_status(request, latest_run.run_id)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao obter DAG Run: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def clear_dag_history(request):
    """Limpa o histórico de execuções do DAG"""
    try:
        # Deletar todos os DAG Runs e Task Instances
        DAGRun.objects.all().delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Histórico limpo com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao limpar histórico: {str(e)}'
        }, status=500) 