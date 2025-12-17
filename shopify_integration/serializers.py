from rest_framework import serializers
from .models import ShopifyOrder


class ShopifyOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopifyOrder
        fields = "__all__"
        read_only_fields = ['local_created_at', 'local_updated_at']
