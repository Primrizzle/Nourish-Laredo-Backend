from rest_framework import serializers
from .models import VolunteerProfile, Event, Donation

class EventSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    
    class Meta:
        model = Event
        fields = "__all__"


class VolunteerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerProfile
        fields = "__all__"

class DonationSerializer(serializers.ModelSerializer):
      class Meta:
        model = Donation
        fields = "__all__"
        read_only_fields = (
            "status",
            "payment_processor",
            "processor_reference_id",
            "created_at",
        )