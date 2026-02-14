from django.urls import path
from core.views import (
    event_list,
    volunteer_signup,
    stripe_webhook,
    create_checkout_session,
    get_partners,
    contact_submit,
    partner_inquiry_submit,
    newsletter_subscribe,
    test_cloudinary_connection,
    debug_env,
    )

urlpatterns = [
    path("events/", event_list, name="event-list"),
    path("volunteer-signup/", volunteer_signup),
    path('donations/webhook/', stripe_webhook, name='stripe_webhook'),
    path("donations/checkout/", create_checkout_session),
    path('partners/', get_partners, name='get_partners'),
    path("contact/", contact_submit, name="contact_submit"),
    path("partners/inquiry/", partner_inquiry_submit, name="partner_inquiry"),
    path("newsletter/subscribe/", newsletter_subscribe, name="newsletter_subscribe"),
    path('test-cloudinary/', test_cloudinary_connection, name='test_cloudinary'),
    path('debug-env/', debug_env, name='debug_env'),
]