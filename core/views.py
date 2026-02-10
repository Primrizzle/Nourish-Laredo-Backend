import logging
import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Event, VolunteerProfile, Donation, Person
from .serializers import EventSerializer, VolunteerProfileSerializer

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

@api_view(["POST"])
def volunteer_signup(request):
    serializer = VolunteerProfileSerializer(data=request.data)
    if serializer.is_valid():
        profile = serializer.save()
        # (Keeping your existing email logic here)
        send_mail(
            subject="New Volunteer Signup",
            message=f"New volunteer: {profile.full_name}\nEmail: {profile.email}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["volunteer@nourishlaredo.com"],
            fail_silently=True,
        )
        return Response({"message": "Signup submitted successfully"}, status=201)
    return Response(serializer.errors, status=400)


# ========================
# STRIPE CHECKOUT SESSION
# ========================
@api_view(["POST"])
def create_checkout_session(request):
    amount = request.data.get("amount")  # cents
    email = request.data.get("email")
    name = request.data.get("name")
    is_recurring = request.data.get("is_recurring", False)

    if not amount:
        return Response({"error": "Amount required"}, status=400)

    try:
        # Construct the Price Data
        price_data = {
            "currency": "usd",
            "unit_amount": amount,
            "product_data": {"name": "Nourish Laredo Donation"},
        }

        # If recurring, add the interval (e.g., monthly)
        if is_recurring:
            price_data["recurring"] = {"interval": "month"}

        # Create the Session
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
            success_url="http://localhost:5173/donate?success=true",
            cancel_url="http://localhost:5173/donate?canceled=true",
        )

        if not is_recurring:
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

    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    event_type = event["type"]

    # ------------------------------------------
    # CASE 1: One-Time Donation Success
    # ------------------------------------------
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Only handle one-time payments here.
        if session.get("mode") == "payment":
            handle_one_time_payment(session)

    # ------------------------------------------
    # CASE 2: Recurring Donation Success (Subscription)
    # ------------------------------------------
    elif event_type == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        
        # This event fires for the first month AND every subsequent month
        if invoice.get("subscription"):
            handle_recurring_payment(invoice)

    # ------------------------------------------
    # CASE 3: Subscription Cancelled (NEW)
    # ------------------------------------------
    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        handle_subscription_deleted(subscription)

    return HttpResponse(status=200)


# ========================
# HELPER FUNCTIONS
# ========================

def handle_one_time_payment(session):
    """Updates the existing pending donation."""
    session_id = session.get("id")
    try:
        donation = Donation.objects.get(processor_reference_id=session_id)
        
        customer_details = session.get("customer_details") or {}
        person = get_or_create_person(
            customer_details.get("email"), 
            customer_details.get("name")
        )

        donation.status = "succeeded"
        if person:
            donation.person = person
        donation.save()
        logger.info(f"One-time donation {donation.id} succeeded.")
        
    except Donation.DoesNotExist:
        logger.error(f"Donation not found for Session ID: {session_id}")


def handle_recurring_payment(invoice):
    """Creates a new donation record for every successful subscription charge."""
    email = invoice.get("customer_email")
    name = invoice.get("customer_name")
    amount = invoice.get("amount_paid") # Cents
    invoice_id = invoice.get("id")
    
    person = get_or_create_person(email, name)

    Donation.objects.create(
        amount=amount,
        currency="USD",
        status="succeeded",
        payment_processor="stripe",
        processor_reference_id=invoice_id,
        person=person
    )
    logger.info(f"Recurring donation processed for {email}")


def handle_subscription_deleted(subscription):
    """
    Handles when a subscription is canceled.
    Fetches the customer email from Stripe to notify/log.
    """
    customer_id = subscription.get("customer")
    
    try:
        # Fetch customer from Stripe to get the email
        customer = stripe.Customer.retrieve(customer_id)
        email = customer.email
        
        logger.warning(f"Subscription canceled for donor: {email}")
        
        # Send notification email to Admin
        send_mail(
            subject="Recurring Donation Canceled",
            message=f"The recurring donation for {email} has been canceled.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            # Update this email to your real admin email
            recipient_list=["admin@nourishlaredo.com"], 
            fail_silently=True,
        )

    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {e}")


def get_or_create_person(email, name):
    if not email:
        return None
        
    first_name = ""
    last_name = ""
    if name:
        parts = name.strip().split(" ", 1)
        first_name = parts[0]
        if len(parts) > 1:
            last_name = parts[1]

    person, _ = Person.objects.update_or_create(
        email=email,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
        },
    )
    return person