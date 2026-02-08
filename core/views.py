from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Event, VolunteerProfile, Donation
from .serializers import EventSerializer, VolunteerProfileSerializer, DonationSerializer

@api_view(["GET"])
def event_list(request):
    events = Event.objects.all().order_by("-date")
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)

@api_view(["POST"])
def volunteer_signup(request):
    serializer = VolunteerProfileSerializer(data=request.data)

    if serializer.is_valid():
        application = serializer.save()

        # 1️⃣ Email to Nourish Laredo team
        send_mail(
            subject="New Volunteer Signup",
            message=(
                f"New volunteer signup received:\n\n"
                f"Name: {profile.full_name}\n"
                f"Email: {profile.email}\n"
                f"Phone: {profile.phone}\n"
                f"Availability: {profile.availability}\n\n"
                f"Motivation:\n{profile.motivation}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["volunteer@nourishlaredo.com"],
            fail_silently=False,
        )

        # 2️⃣ (Optional but recommended) Confirmation email to volunteer
        send_mail(
            subject="Thanks for volunteering with Nourish Laredo!",
            message=(
                f"Hi {profile.full_name},\n\n"
                "Thank you for signing up to volunteer with Nourish Laredo! "
                "We’ve received your information and someone from our team "
                "will reach out soon.\n\n"
                "We appreciate your willingness to help our community.\n\n"
                "— Nourish Laredo Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[profile.email],
            fail_silently=False,
        )

        return Response(
            {"message": "Signup submitted successfully"},
            status=201
        )

    return Response(serializer.errors, status=400)

@api_view(["POST"])
def create_donation(request):
    serializer = DonationSerializer(data=request.data)

    if serializer.is_valid():
        donation = serializer.save(
            status="pending",
            payment_processor="stripe",
            processor_reference_id="pending"
        )
        return Response(
            {
                "donation_id": donation.id,
                "status": donation.status,
            },
            status=201,
        )

    return Response(serializer.errors, status=400)