from django.urls import path
from .views import event_list, volunteer_signup

urlpatterns = [
    path("events/", event_list, name="event-list"),
    path("volunteer-signup/", volunteer_signup),
]
