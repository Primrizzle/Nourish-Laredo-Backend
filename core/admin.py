from django.contrib import admin
from .models import Event, VolunteerApplication


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "location", "created_at")
    list_filter = ("date",)
    search_fields = ("title", "description", "location")


@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "created_at")
    search_fields = ("full_name", "email")
    list_filter = ("created_at",)
