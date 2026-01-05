from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Event
from .serializers import EventSerializer

@api_view(["GET"])
def event_list(request):
    events = Event.objects.all().order_by("-date")
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)
