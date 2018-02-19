from django.db import models

class TrainingData(models.Model):
    exact_match = models.IntegerField(blank=True, default=0)
    term_overlap = models.FloatField(blank=True, default=0)
    answer_length = models.FloatField(blank=True, default=0)
    semantic_score = models.FloatField(blank=True, default=0)
    has_code = models.IntegerField(blank=True, default=0)
    intent = models.IntegerField(blank=True, default=0)
    bm25_qrelevance = models.FloatField(blank=True, default=0)
    qscore = models.IntegerField(blank=True, default=0)
    view_count = models.IntegerField(blank=True, default=0)
    ascore = models.IntegerField(blank=True, default=0)
    is_accepted_answer = models.IntegerField(blank=True, default=0)
    label = models.IntegerField(blank=True, default=0)
    uid = models.IntegerField(unique=True)
