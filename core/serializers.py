from rest_framework import serializers
from .models import VolunteerApplication, Event

class EventSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    
    class Meta:
        model = Event
        fields = "__all__"


class VolunteerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerApplication
        fields = "__all__"
