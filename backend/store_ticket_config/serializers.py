from rest_framework import serializers
from .models import *

class TickerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ticketConfig
        fields = '__all__'