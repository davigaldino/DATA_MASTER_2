from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import pandas as pd
import json
import uuid
import os
from .models import ETLSession, ETLLog
from .etl_processor import ETLProcessor

def etl_demo_view(request):
    """Renderiza a página principal do ETL Demo."""
    return render(request, 'etl_demo/demo.html')

@csrf_exempt
@require_http_methods(["POST"])
def upload_csv(request):
    """Processa o upload do arquivo CSV."""
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'Nenhum arquivo enviado'}, status=400)
    
    file = request.FILES['file']
    
    # Validações básicas
    if not file.name.endswith('.csv'):
        return JsonResponse({'error': 'Apenas arquivos CSV são aceitos'}, status=400)
    
    # Criar sessão
    session = ETLSession.objects.create(
        filename=file.name,
        status='uploaded'
    )
    
    # Salvar arquivo temporariamente
    file_path = f'/tmp/{session.session_id}_{file.name}'
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    # Validação inicial do CSV
    try:
        df = pd.read_csv(file_path, nrows=5)  # Apenas preview
        session.total_rows = len(pd.read_csv(file_path))
        session.save()
        
        ETLLog.objects.create(
            session=session,
            level='INFO',
            message=f'Arquivo {file.name} carregado com sucesso. {session.total_rows} linhas detectadas.',
            step='upload'
        )
        
        return JsonResponse({
            'session_id': str(session.session_id),
            'filename': file.name,
            'total_rows': session.total_rows,
            'preview': df.to_dict('records')
        })
        
    except Exception as e:
        session.status = 'error'
        session.save()
        
        ETLLog.objects.create(
            session=session,
            level='ERROR',
            message=f'Erro ao processar arquivo: {str(e)}',
            step='upload'
        )
        
        return JsonResponse({'error': f'Erro ao processar arquivo: {str(e)}'}, status=400)

def get_processing_status(request, session_id):
    """Retorna o status atual do processamento."""
    try:
        session = ETLSession.objects.get(session_id=session_id)
        logs = session.logs.order_by('-timestamp')[:10]
        
        # Preparar estatísticas detalhadas
        detailed_stats = {}
        if hasattr(session, 'metadata') and session.metadata:
            detailed_stats = session.metadata.get('cleaning_stats', {})
        
        return JsonResponse({
            'session_id': str(session.session_id),
            'status': session.status,
            'current_step': session.current_step,
            'progress': session.progress,
            'stats': {
                'total_rows': session.total_rows,
                'processed_rows': session.processed_rows,
                'cleaned_rows': session.cleaned_rows,
                'error_count': session.error_count
            },
            'detailed_stats': detailed_stats,
            'logs': [
                {
                    'timestamp': timezone.localtime(log.timestamp).strftime('%H:%M:%S'),
                    'level': log.level,
                    'message': log.message,
                    'step': log.step
                } for log in logs
            ]
        })
        
    except ETLSession.DoesNotExist:
        return JsonResponse({'error': 'Sessão não encontrada'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def process_csv(request, session_id):
    """Inicia o processamento do CSV."""
    try:
        session = ETLSession.objects.get(session_id=session_id)
        
        # Iniciar processamento assíncrono
        processor = ETLProcessor(session)
        processor.start_processing()
        
        return JsonResponse({'message': 'Processamento iniciado'})
        
    except ETLSession.DoesNotExist:
        return JsonResponse({'error': 'Sessão não encontrada'}, status=404) 