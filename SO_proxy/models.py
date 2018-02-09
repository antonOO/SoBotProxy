from django.db import models

class TrainingData(models.Model):
    exact_match = models.IntegerField(blank=True, default=0)
    term_overlap = models.FloatField(blank=True, default=0)
    synonym_overlap = models.FloatField(blank=True, default=0)
    language_model_score = models.FloatField(blank=True, default=0)
    sentence_length = models.FloatField(blank=True, default=0)
    sentence_location = models.FloatField(blank=True, default=0)
    esa = models.FloatField(blank=True, default=0)
    word_embedding = models.FloatField(blank=True, default=0)
    entity_linking = models.FloatField(blank=True, default=0)
    has_code = models.IntegerField(blank=True, default=0)
    label = models.IntegerField(blank=True, default=0)
