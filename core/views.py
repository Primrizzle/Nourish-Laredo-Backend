from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Event, VolunteerApplication
from .serializers import EventSerializer, VolunteerApplicationSerializer

@api_view(["GET"])
def event_list(request):
    events = Event.objects.all().order_by("-date")
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)

@api_view(["POST"])
def volunteer_signup(request):
    serializer = VolunteerApplicationSerializer(data=request.data)

    if serializer.is_valid():
        application = serializer.save()

        # 1️⃣ Email to Nourish Laredo team
        send_mail(
            subject="New Volunteer Application Submitted",
            message=(
                f"New volunteer application received:\n\n"
                f"Name: {application.full_name}\n"
                f"Email: {application.email}\n"
                f"Phone: {application.phone}\n"
                f"Availability: {application.availability}\n\n"
                f"Motivation:\n{application.motivation}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["volunteer@nourishlaredo.com"],
            fail_silently=False,
        )

        # 2️⃣ (Optional but recommended) Confirmation email to volunteer
        send_mail(
            subject="Thanks for volunteering with Nourish Laredo!",
            message=(
                f"Hi {application.full_name},\n\n"
                "Thank you for signing up to volunteer with Nourish Laredo! "
                "We’ve received your application and someone from our team "
                "will reach out soon.\n\n"
                "We appreciate your willingness to help our community.\n\n"
                "— Nourish Laredo Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.email],
            fail_silently=False,
        )

        return Response(
            {"message": "Application submitted successfully"},
            status=201
        )

    return Response(serializer.errors, status=400)
