"""
apps/predictions/models.py
Stores prediction session history for logged-in users.
"""
import uuid
from django.db import models
from django.conf import settings


class PredictionSession(models.Model):
    class Status(models.TextChoices):
        COMPLETED = 'completed', 'Completed'
        FAILED    = 'failed',    'Failed'

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                      related_name='prediction_sessions')
    neet_rank     = models.PositiveIntegerField()
    neet_score    = models.PositiveSmallIntegerField(null=True, blank=True)
    category      = models.CharField(max_length=10)
    state         = models.CharField(max_length=60, blank=True)
    quota         = models.CharField(max_length=5, blank=True)
    total_results = models.PositiveSmallIntegerField(default=0)
    status        = models.CharField(max_length=15, choices=Status.choices, default=Status.COMPLETED)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prediction_sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f'Session {self.id} | Rank {self.neet_rank} | {self.category}'

class CollegeCutoff(models.Model):
    college_name = models.CharField(max_length=255, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    city = models.CharField(max_length=100)
    college_type = models.CharField(max_length=50)
    quota = models.CharField(max_length=50, db_index=True)
    category = models.CharField(max_length=50, db_index=True)
    opening_rank = models.IntegerField()
    closing_rank = models.IntegerField(db_index=True)
    annual_fee = models.FloatField()
    year = models.IntegerField(db_index=True)
    mbbs_seats = models.IntegerField(default=0)
    nmc_ranking = models.IntegerField(null=True, blank=True)
    course_type = models.CharField(max_length=50, default='MBBS', db_index=True)
    bond_years = models.IntegerField(default=0)
    bond_penalty = models.FloatField(default=0.0)

    class Meta:
        db_table = 'college_cutoffs'
        ordering = ['closing_rank']

    def __str__(self):
        return f"{self.college_name} ({self.course_type}) - Rank {self.closing_rank}"
