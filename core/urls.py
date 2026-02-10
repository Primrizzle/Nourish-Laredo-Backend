from django.urls import path
from core.views import (
    event_list,
    volunteer_signup,
    stripe_webhook,
    create_checkout_session,
)

urlpatterns = [
    path("events/", event_list, name="event-list"),
    path("volunteer-signup/", volunteer_signup),
    path('donations/webhook/', stripe_webhook, name='stripe_webhook'),
    path("donations/checkout/", create_checkout_session),
]