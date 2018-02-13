from django.db import models

class TrainingData(models.Model):
    exact_match = models.IntegerField(blank=True, default=0)
    term_overlap = models.FloatField(blank=True, default=0)
    answer_length = models.FloatField(blank=True, default=0)
    semantic_score = models.FloatField(blank=True, default=0)
    has_code = models.IntegerField(blank=True, default=0)
    label = models.IntegerField(blank=True, default=0)
