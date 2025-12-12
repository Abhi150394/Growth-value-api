from rest_framework import serializers
from .models import LightspeedOrder


class LightspeedOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LightspeedOrder
        fields = "__all__"
        read_only_fields = ['created_at', 'updated_at']
