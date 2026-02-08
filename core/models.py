import uuid
from django.db import models

class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField()
    location = models.CharField(max_length=255)

    image = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    is_highlight = models.BooleanField(
        default=False,
        help_text="Show in Past Events Highlights"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class VolunteerProfile(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    availability = models.CharField(max_length=255, blank=True)
    motivation = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.email})"

class Person(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

class Donation(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    person = models.ForeignKey(
        "Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donations",
        help_text="Null for anonymous donations"
    )

    event = models.ForeignKey(
        "Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donations"
    )

    amount = models.PositiveIntegerField(
        help_text="Amount in smallest currency unit (e.g., cents)"
    )

    currency = models.CharField(
        max_length=10,
        default="USD"
    )

    status = models.CharField(
        max_length=50,
        help_text="Donation status (pending, succeeded, failed)"
    )

    payment_processor = models.CharField(
        max_length=50,
        default="stripe"
    )

    processor_reference_id = models.CharField(
        max_length=255,
        help_text="PaymentIntent or transaction ID"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} {self.currency} ({self.status})"