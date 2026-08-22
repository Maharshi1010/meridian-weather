from django.contrib import admin
from .models import SavedCity


@admin.register(SavedCity)
class SavedCityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'session_key', 'added_at')
    list_filter = ('country',)
    search_fields = ('name', 'country')
