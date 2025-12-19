from rest_framework import serializers
from .models import LightspeedOrder, LightspeedProduct, LightspeedProductGroup


class LightspeedOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LightspeedOrder
        fields = "__all__"
        read_only_fields = ['created_at', 'updated_at']


class LightspeedProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LightspeedProduct
        fields = "__all__"
        read_only_fields = ['created_at', 'updated_at']


class LightspeedProductGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = LightspeedProductGroup
        fields = "__all__"
        read_only_fields = ['created_at', 'updated_at']
