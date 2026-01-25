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
        serializer.save()
        return Response(
            {"message": "Application submitted successfully"},
            status=201
        )

    return Response(serializer.errors, status=400)