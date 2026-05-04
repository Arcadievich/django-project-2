from django.contrib import admin

from .models import PlaceCoordinates


@admin.register(PlaceCoordinates)
class PlaceCoordinatesAdmin(admin.ModelAdmin):
    search_fields = ['address',]
    list_display = ['address', 'lat', 'lon', 'created_at']