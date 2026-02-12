from django.contrib import admin
from .models import (
    Event, 
    VolunteerProfile, 
    Person, 
    Donation, 
    Partner,
    ContactMessage,
    PartnerInquiry,
)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "location", "created_at")
    list_filter = ("date",)
    search_fields = ("title", "description", "location")


@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "created_at")
    search_fields = ("full_name", "email")
    list_filter = ("created_at",)

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "created_at")
    search_fields = ("email", "first_name", "last_name")

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        "amount",
        "currency",
        "status",
        "payment_processor",
        "created_at",
    )
    list_filter = ("status", "currency", "payment_processor")
    search_fields = ("processor_reference_id",)

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    readonly_fields = ('created_at',) # Keep the timestamp uneditable
    search_fields = ('name', 'email', 'message')

@admin.register(PartnerInquiry)
class PartnerInquiryAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'contact_name', 'partnership_type', 'created_at')
    list_filter = ('partnership_type',)