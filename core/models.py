from django.db import models

class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField()
    location = models.CharField(max_length=255)

    image = models.ImageField(
        upload_to="events/",
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
