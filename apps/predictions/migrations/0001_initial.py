from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name='PredictionSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('neet_rank', models.PositiveIntegerField()),
                ('category', models.CharField(max_length=10)),
                ('state', models.CharField(blank=True, max_length=60)),
                ('quota', models.CharField(blank=True, max_length=5)),
                ('total_results', models.PositiveSmallIntegerField(default=0)),
                ('status', models.CharField(
                    choices=[('completed', 'Completed'), ('failed', 'Failed')],
                    default='completed', max_length=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='prediction_sessions',
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'prediction_sessions', 'ordering': ['-created_at']},
        ),
    ]
