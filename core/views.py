import logging
import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status  

from .models import *
from .serializers import *

from django.http import JsonResponse
import cloudinary.api

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

# core/views.py

@api_view(['POST'])
def volunteer_signup(request):
    serializer = VolunteerProfileSerializer(data=request.data)
    if serializer.is_valid():
        volunteer = serializer.save()

        # 1. Email to ADMIN
        # CHANGED: volunteer.message -> volunteer.motivation
        send_mail(
            "New Volunteer Signup",
            f"New volunteer: {volunteer.full_name}\n"
            f"Email: {volunteer.email}\n"
            f"Phone: {volunteer.phone}\n"
            f"Motivation: {volunteer.motivation}", 
            "noreply@nourishlaredo.org",
            ["volunteer@nourishlaredo.com"],
        )

        # 2. Email to VOLUNTEER
        send_mail(
            "Welcome to Nourish Laredo!",
            f"Hi {volunteer.full_name},\n\n"
            f"Thank you for signing up to volunteer with us! We've received your application and will be in touch soon.",
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

@api_view(['GET'])
def get_partners(request):
    partners = Partner.objects.all().order_by('name') # Newest first
    serializer = PartnerSerializer(partners, many=True)
    return Response(serializer.data)

# core/views.py

@api_view(["POST"])
def contact_submit(request):
    """
    Handles Contact Us form submissions.
    1. Saves the message to the database.
    2. Emails the Admin with the details.
    3. Emails the User a nice confirmation receipt.
    """
    serializer = ContactMessageSerializer(data=request.data)
    
    if serializer.is_valid():
        contact = serializer.save()

        # ==========================
        # 1. NOTIFY ADMIN (You)
        # ==========================
        send_mail(
            subject=f"New Contact: {contact.subject or 'General Inquiry'}",
            message=(
                f"You received a new message from the website:\n\n"
                f"Name: {contact.name}\n"
                f"Email: {contact.email}\n"
                f"Subject: {contact.subject}\n\n"
                f"Message:\n{contact.message}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["info@nourishlaredo.com"], # Your real admin email
            fail_silently=True,
        )

        # ==========================
        # 2. AUTO-REPLY TO USER (Them)
        # ==========================
        user_subject = "We've received your message! - Nourish Laredo"
        user_message = (
            f"Hi {contact.name},\n\n"
            f"Thank you for reaching out to Nourish Laredo! We have received your message regarding '{contact.subject}' and our team is reviewing it.\n\n"
            f"We are a small but passionate team, so please allow us 24-48 hours to get back to you. \n\n"
            f"In the meantime, feel free to check our Events page for upcoming volunteer opportunities.\n\n"
            f"With gratitude,\n"
            f"The Nourish Laredo Team\n"
            f"www.nourishlaredo.org"
        )

        send_mail(
            subject=user_subject,
            message=user_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[contact.email], # Sends to the user who filled the form
            fail_silently=True,
        )

        return Response({"message": "Message sent and confirmation emailed!"}, status=201)

    return Response(serializer.errors, status=400)

# core/views.py

@api_view(["POST"])
def partner_inquiry_submit(request):
    serializer = PartnerInquirySerializer(data=request.data)
    if serializer.is_valid():
        inquiry = serializer.save()
        
        # ==========================
        # 1. NOTIFY ADMIN (You)
        # ==========================
        send_mail(
            subject=f"New Partner Inquiry: {inquiry.organization_name}",
            message=(
                f"Organization: {inquiry.organization_name}\n"
                f"Contact: {inquiry.contact_name}\n"
                f"Email: {inquiry.email}\n"
                f"Phone: {inquiry.phone}\n"
                f"Website: {inquiry.website}\n"
                f"Type: {inquiry.get_partnership_type_display()}\n\n"
                f"Message:\n{inquiry.message}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["partners@nourishlaredo.com"], # Your admin email
            fail_silently=True,
        )

        # ==========================
        # 2. AUTO-REPLY TO PARTNER (Them)
        # ==========================
        user_subject = "Thank you for your interest in partnering with Nourish Laredo"
        user_message = (
            f"Hi {inquiry.contact_name},\n\n"
            f"Thank you for reaching out on behalf of {inquiry.organization_name}! "
            f"We are thrilled that you are interested in joining our mission through {inquiry.get_partnership_type_display().lower()}.\n\n"
            f"Our partnership team is reviewing your inquiry and will be in touch shortly to discuss next steps.\n\n"
            f"Together, we can make a lasting impact on our community.\n\n"
            f"Warmly,\n"
            f"The Nourish Laredo Team\n"
            f"www.nourishlaredo.com"
        )

        send_mail(
            subject=user_subject,
            message=user_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[inquiry.email], # Sends to the partner
            fail_silently=True,
        )

        return Response({"message": "Inquiry received and confirmation sent!"}, status=201)
    
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def newsletter_subscribe(request):
    serializer = NewsletterSubscriberSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Subscribed successfully!"}, status=201)
    
    if 'email' in serializer.errors:
        error_msg = str(serializer.errors['email'][0])
        if "already exists" in error_msg:
            return Response({"message": "You are already subscribed!"}, status=200)

    return Response(serializer.errors, status=400)

def test_cloudinary_connection(request):
    try:
        # The ping() method verifies if your credentials are valid
        response = cloudinary.api.ping()
        return JsonResponse({
            "status": "Success",
            "message": "Django is successfully talking to Cloudinary!",
            "response": response
        })
    except Exception as e:
        return JsonResponse({
            "status": "Error",
            "message": str(e)
        }, status=500)

@api_view(['GET'])
def debug_env(request):
    import os
    return Response({
        'has_cloudinary_url': 'CLOUDINARY_URL' in os.environ,
        'cloudinary_url_length': len(os.environ.get('CLOUDINARY_URL', ''))
    })

@api_view(['GET'])
def debug_env(request):
    import os
    from decouple import config
    import cloudinary
    
    cloudinary_url_from_env = os.environ.get('CLOUDINARY_URL', '')
    cloudinary_url_from_config = config('CLOUDINARY_URL', default='')
    
    return Response({
        'env_has_it': bool(cloudinary_url_from_env),
        'config_has_it': bool(cloudinary_url_from_config),
        'env_starts_with': cloudinary_url_from_env[:20] if cloudinary_url_from_env else '',
        'config_starts_with': cloudinary_url_from_config[:20] if cloudinary_url_from_config else '',
        'cloudinary_config_cloud_name': cloudinary.config().cloud_name,
        'cloudinary_config_api_key': cloudinary.config().api_key,
        'cloudinary_config_has_secret': bool(cloudinary.config().api_secret)
    })