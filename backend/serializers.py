import logging

from rest_framework import serializers
from .models import UserData, Payment, Searches, Orders, Wishlist, Products, Scraper, Vendor, Tag

_logger = logging.getLogger(__name__)


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"
    
    def to_internal_value(self, data):
        if 'website' in data and not (data['website'].startswith('https') or data['website'].startswith('http')):
            data['website'] = 'https://' + data['website']
        if "name" in data:
            data["name"] = (data.get("name","")).capitalize()
        return super().to_internal_value(data)

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    vendors = VendorSerializer(many=True, required=False)
    tags = TagSerializer(many=True, required=False)
    class Meta:
        model = UserData
        fields = [
            "id",
            "email",
            "name", 
            "role",
            "password", 
            "phone", 
            "dob",
            "gender",
            "vat", 
            "business",
            "tags",
            "business_address",
            "website_url", 
            "vendors",
            "i_address",
            "i_country", 
            "i_zip",
            "a_address",
            "a_country",
            "a_zip"
        ]

    def validate(self, data):
        vendors = data.get('vendors', [])
        vendor_serializer = VendorSerializer(data=vendors, many=True)
        vendor_serializer.is_valid(raise_exception=True)
        return data
    
    def create(self, validated_data):
        
        try:
            vendors_data = validated_data.pop('vendors', [])
            tag_list = validated_data.pop("tags", [])
            user = UserData.objects.create(
                email=validated_data.get("email"),
                name=validated_data.get("name"),
                phone=validated_data.get("phone"),
                dob=validated_data.get("dob"),
                vat=validated_data.get("vat"),
                business=validated_data.get("business"),
                business_address = validated_data.get("business_address"),
                website_url = validated_data.get("website_url"),
                gender=validated_data.get("gender"),
                i_address=validated_data.get("i_address"),
                i_country=validated_data.get("i_country"),
                i_zip=validated_data.get("i_zip"),
                a_address=validated_data.get("a_address"),
                a_country=validated_data.get("a_country"),
                a_zip=validated_data.get("a_zip")
            )
        except:
            user = UserData.objects.create(
                email=validated_data.get("email"),
                name=validated_data.get("name"),
                phone=validated_data.get("phone"),
                dob=validated_data.get("dob"),
                vat=validated_data.get("vat"),
                business=validated_data.get("business"),
                business_address = validated_data.get("business_address"),
                website_url = validated_data.get("website_url"),
                gender=validated_data.get("gender"),
                i_address=validated_data.get("i_address"),
                i_country=validated_data.get("i_country"),
                i_zip=validated_data.get("i_zip")
            )

        user.set_password(validated_data['password'])
        user.set_tags(tag_list)
        user.set_vendors(vendors_data)
        user.save()
        
        return user

    def update(self, instance, validated_data):
        user = UserData.objects.get(id=instance.id)
        try:
            user.name = validated_data['name']
        except:
            user.name = instance.name

        try:
            user.email = validated_data['email']
        except:
            user.email = instance.email

        try:
            user.phone = validated_data['phone']
        except:
            user.phone = instance.phone
        
        try:
            user.dob = validated_data['dob']
        except:
            user.dob = instance.dob
        
        try:
            user.vat = validated_data["vat"]
        except:
            user.vat = instance.vat
        
        try:
            user.business = validated_data["business"]
        except:
            user.business = instance.business
        
        try:
            tags = validated_data.get("tags", [])
            if tags:
                user.set_tags(tags)
        except:
            _logger.error(f"Unable to set Tag. User:{self.name}, Tags:{tags}, error:{e}")
            # user.tags = instance.tags
        
        try:
            vendors_data = validated_data.get("vendors") or []
            if vendors_data:
                user.set_vendors(vendors_data)
        except Exception as e:
            _logger.error(f"Unable to add Vendors. User:{self.name}, Vendors list:{vendors_data}, error:{e}")
        
        try:
            user.business_address = validated_data["business_address"]
        except:
            user.business_address = instance.business_address
        
        try:
            user.website_url = validated_data["website_url"]
        except:
            user.website_url = instance.website_url
        
        try:
            user.gender = validated_data['gender']
        except:
            user.gender = instance.gender

        try:
            user.i_address = validated_data['i_address']
        except:
            user.i_address = instance.i_address
        
        try:
            user.i_country = validated_data['i_country']
        except:
            user.i_country = instance.i_country
        
        try:
            user.i_zip = validated_data['i_zip']
        except:
            user.i_zip = instance.i_zip

        try:
            user.a_address = validated_data['a_address']
        except:
            user.a_address = instance.a_address
        
        try:
            user.a_country = validated_data['a_country']
        except:
            user.a_country = instance.a_country

        try:
            user.a_zip = validated_data['a_zip']
        except:
            user.a_zip = instance.a_zip

        try:
            user.set_password(validated_data['password'])
        except:
            pass
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    vendors = VendorSerializer(many=True, required=False)
    tags = TagSerializer(many=True, required=False)
    class Meta:
        model = UserData
        fields = [
            "id",
            "email",
            "name",
            "role",
            "phone",
            "dob",
            "gender",
            "vat",
            "business",
            "tags",
            "business_address",
            "website_url",
            "vendors",
            "i_address",
            "i_country",
            "i_zip",
            "a_address",
            "a_country",
            "a_zip",
            "date_joined",
            'paid',
            'payment_status'
        ]
        
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()

        exclude_fields = self.context.get('exclude_fields', [])
        for field in exclude_fields:
            # providing a default prevents a KeyError
            # if the field does not exist
            fields.pop(field, default=None)

        return fields
    
class SearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Searches
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()

        exclude_fields = self.context.get('exclude_fields', [])
        for field in exclude_fields:
            # providing a default prevents a KeyError
            # if the field does not exist
            fields.pop(field, default=None)

        return fields
    
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()

        exclude_fields = self.context.get('exclude_fields', [])
        for field in exclude_fields:
            # providing a default prevents a KeyError
            # if the field does not exist
            fields.pop(field, None)

        return fields
    
class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()

        exclude_fields = self.context.get('exclude_fields', [])
        for field in exclude_fields:
            # providing a default prevents a KeyError
            # if the field does not exist
            fields.pop(field, default=None)

        return fields
    
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()

        exclude_fields = self.context.get('exclude_fields', [])
        for field in exclude_fields:
            # providing a default prevents a KeyError
            # if the field does not exist
            fields.pop(field, default=None)
        return fields
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.price == 0.0:
            representation['price'] = -1.0
        return representation
    
class ScraperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scraper
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()

        exclude_fields = self.context.get('exclude_fields', [])
        for field in exclude_fields:
            
            # providing a default prevents a KeyError
            # if the field does not exist
            fields.pop(field, default=None)

        return fields