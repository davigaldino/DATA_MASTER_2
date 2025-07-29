# Generated manually for ETL Demo app

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ETLSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('filename', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('uploaded', 'Uploaded'), ('validating', 'Validating'), ('cleaning', 'Cleaning'), ('transforming', 'Transforming'), ('loading', 'Loading'), ('completed', 'Completed'), ('error', 'Error')], default='uploaded', max_length=20)),
                ('current_step', models.CharField(blank=True, max_length=50)),
                ('progress', models.IntegerField(default=0)),
                ('total_rows', models.IntegerField(default=0)),
                ('processed_rows', models.IntegerField(default=0)),
                ('cleaned_rows', models.IntegerField(default=0)),
                ('error_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ETLLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('level', models.CharField(choices=[('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error')], max_length=10)),
                ('message', models.TextField()),
                ('step', models.CharField(max_length=50)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='etl_demo.etlsession')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ] 