import logging
import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

import cloudinary.api
from .models import Event, VolunteerProfile, Donation, Person, Partner
from .serializers import (
    EventSerializer, VolunteerProfileSerializer, 
    DonationSerializer, ContactMessageSerializer, 
    PartnerSerializer, PartnerInquirySerializer, 
    NewsletterSubscriberSerializer
)

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

# ========================
# EVENTS & VOLUNTEERS 
# ========================
@api_view(["GET"])
def event_list(request):
    events = Event.objects.all().order_by("-date")
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def volunteer_signup(request):
    serializer = VolunteerProfileSerializer(data=request.data)
    if serializer.is_valid():
        volunteer = serializer.save()
        send_mail(
            "New Volunteer Signup",
            f"New volunteer: {volunteer.full_name}\nEmail: {volunteer.email}\nPhone: {volunteer.phone}\nMotivation: {volunteer.motivation}", 
            "noreply@nourishlaredo.org",
            ["volunteer@nourishlaredo.com"],
        )
        send_mail(
            "Welcome to Nourish Laredo!",
            f"Hi {volunteer.full_name},\n\nThank you for signing up to volunteer with us!",
            "noreply@nourishlaredo.org",
            [volunteer.email],
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ========================
# STRIPE CHECKOUT SESSION
# ========================
@api_view(["POST"])
def create_checkout_session(request):
    amount = request.data.get("amount")
    email = request.data.get("email")
    name = request.data.get("name")
    is_recurring = request.data.get("is_recurring", False)

    if not amount:
        return Response({"error": "Amount required"}, status=400)

    try:
        price_data = {
            "currency": "usd",
            "unit_amount": amount,
            "product_data": {"name": "Nourish Laredo Donation"},
        }
        if is_recurring:
            price_data["recurring"] = {"interval": "month"}

        # PRODUCTION URLs - Replace localhost with your live domain
        session = stripe.checkout.Session.create(
            mode="subscription" if is_recurring else "payment",
            payment_method_types=["card"],
            billing_address_collection="required",
            customer_creation="always",
            customer_email=email if email else None,
            metadata={
                "email": email or "",
                "name": name or "",
                "type": "recurring" if is_recurring else "one_time"
            },
            line_items=[{"price_data": price_data, "quantity": 1}],
            success_url="https://www.nourishlaredo.com/donate?success=true",
            cancel_url="https://www.nourishlaredo.com/donate?canceled=true",
        )

        if not is_recurring:
            # We save the session ID so the webhook can find this record later
            Donation.objects.create(
                amount=amount,
                currency="USD",
                status="pending",
                payment_processor="stripe",
                processor_reference_id=session.id,
            )

        return Response({"url": session.url})
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return Response({"error": str(e)}, status=500)

# ========================
# STRIPE WEBHOOK
# ========================
@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    event_type = event["type"]

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        if session.get("mode") == "payment":
            handle_one_time_payment(session)
    elif event_type == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        if invoice.get("subscription"):
            handle_recurring_payment(invoice)
    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        handle_subscription_deleted(subscription)

    return HttpResponse(status=200)

# ========================
# HELPER FUNCTIONS
# ========================
def handle_one_time_payment(session):
    session_id = session.get("id")
    try:
        donation = Donation.objects.get(processor_reference_id=session_id)
        customer_details = session.get("customer_details") or {}
        person = get_or_create_person(customer_details.get("email"), customer_details.get("name"))
        
        donation.status = "succeeded"
        if person:
            donation.person = person
        donation.save()
        logger.info(f"One-time donation {donation.id} succeeded.")
    except Donation.DoesNotExist:
        logger.error(f"Donation not found for Session ID: {session_id}")

def handle_recurring_payment(invoice):
    email = invoice.get("customer_email")
    name = invoice.get("customer_name")
    amount = invoice.get("amount_paid")
    invoice_id = invoice.get("id")
    person = get_or_create_person(email, name)

    Donation.objects.create(
        amount=amount, currency="USD", status="succeeded",
        payment_processor="stripe", processor_reference_id=invoice_id, person=person
    )

def handle_subscription_deleted(subscription):
    customer_id = subscription.get("customer")
    try:
        customer = stripe.Customer.retrieve(customer_id)
        send_mail(
            "Recurring Donation Canceled",
            f"The recurring donation for {customer.email} has been canceled.",
            settings.DEFAULT_FROM_EMAIL, ["admin@nourishlaredo.com"], fail_silently=True
        )
    except Exception as e:
        logger.error(f"Error handling cancellation: {e}")

def get_or_create_person(email, name):
    if not email: return None
    first_name, last_name = "", ""
    if name:
        parts = name.strip().split(" ", 1)
        first_name = parts[0]
        if len(parts) > 1: last_name = parts[1]
    person, _ = Person.objects.update_or_create(
        email=email, defaults={"first_name": first_name, "last_name": last_name}
    )
    return person

# ========================
# PARTNERS & CONTACT
# ========================
@api_view(['GET'])
def get_partners(request):
    partners = Partner.objects.all().order_by('name')
    serializer = PartnerSerializer(partners, many=True)
    return Response(serializer.data)

@api_view(["POST"])
def contact_submit(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        contact = serializer.save()
        send_mail(f"New Contact: {contact.subject}", f"From: {contact.name}\n{contact.message}", settings.DEFAULT_FROM_EMAIL, ["info@nourishlaredo.com"])
        return Response({"message": "Message sent!"}, status=201)
    return Response(serializer.errors, status=400)

@api_view(["POST"])
def partner_inquiry_submit(request):
    serializer = PartnerInquirySerializer(data=request.data)
    if serializer.is_valid():
        inquiry = serializer.save()
        send_mail(f"New Partner Inquiry: {inquiry.organization_name}", f"Contact: {inquiry.contact_name}", settings.DEFAULT_FROM_EMAIL, ["partners@nourishlaredo.com"])
        return Response({"message": "Inquiry received!"}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def newsletter_subscribe(request):
    serializer = NewsletterSubscriberSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Subscribed!"}, status=201)
    return Response(serializer.errors, status=400)

def test_cloudinary_connection(request):
    try:
        response = cloudinary.api.ping()
        return JsonResponse({"status": "Success", "response": response})
    except Exception as e:
        return JsonResponse({"status": "Error", "message": str(e)}, status=500)