from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    
    class Meta:
        model = Event
        fields = "__all__"
