from django.db import models


class SavedCity(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=10, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    session_key = models.CharField(max_length=40, db_index=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        unique_together = ('name', 'country', 'session_key')
        verbose_name_plural = 'Saved cities'

    def __str__(self):
        return f"{self.name}, {self.country}"
