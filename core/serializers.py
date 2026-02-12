from rest_framework import serializers
from .models import VolunteerProfile, Event, Donation, Partner, PartnerInquiry, NewsletterSubscriber

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

class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ['id', 'name', 'description', 'website', 'logo']

from .models import ContactMessage

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at']

class PartnerInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerInquiry
        fields = '__all__'

class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']