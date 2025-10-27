from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

import logging

_logger = logging.getLogger(__name__)

# Create your models here.
class UserManager(BaseUserManager):

    use_in_migration = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is Required')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff = True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser = True')

        return self.create_user(email, password, **extra_fields)


class UserData(AbstractUser):
    username = None
    name = models.CharField("Name", max_length=100)
    paid = models.BooleanField(default=False)
    payment_status = models.BooleanField(default=False)
    customer_id = models.CharField(max_length=200, default='', blank=True, null=True)
    role = models.CharField("Role", max_length=36, default="user")
    phone = models.CharField('Phone', max_length=20, unique=True)
    dob = models.DateField("Date of Birth", null=True, blank=True)
    gender = models.CharField(max_length=12, null=True, blank=True)
    i_address = models.CharField(max_length=400, null=True, default="", blank=True)
    i_country = models.CharField(max_length=64)
    i_zip = models.IntegerField(default='0')
    a_address = models.CharField(max_length=400, null=True, default="", blank=True)
    a_country = models.CharField(max_length=64, null=True, default="", blank=True)
    a_zip = models.IntegerField(null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True)
    vat = models.CharField("Vat", max_length=16, default="")
    business = models.CharField("Business", max_length=120, default="")
    business_address = models.CharField(max_length=160, null=True, default="", blank=True)
    vendors = models.ManyToManyField(
        "backend.Vendor",
        related_name="users_data",
        blank=True
    )
    tags = models.ManyToManyField(
        "backend.Tag",
        related_name='tags',
        blank=True,
    )
    website_url = models.CharField("Website", max_length=64, null=True, default="", blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    allow_access = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name','phone']

    def __str__(self):
        return self.name
    
    def set_tags(self, tag_list=[]):
        tags=[]
        for tag_data in tag_list:
            tag, created = Tag.objects.get_or_create(**tag_data)
            tags.append(tag)
        if tags:
            self.tags.set(tags)
        return self
    
    def set_vendors(self, vendors_data=[]):
        try:
            vendors = []
            for data in vendors_data:
                vendor, created = Vendor.objects.get_or_create(website=data.get("website"), defaults=data)
                vendors.append(vendor)
            
            self.vendors.set(vendors)
            return self
        except Exception as exc:
            _logger.error(f"Unable to add Vendors. user:{self.name}, vendors list:{vendors_data}, error: {exc}")
    
    def saved_product_ids(self):
        ids=[]
        ids = list(self.wishlists.filter(is_deleted=False).values_list("product__id", flat=True))
        return ids
    
class UserDataResetPassword(models.Model):
    customer = models.OneToOneField(UserData, on_delete=models.CASCADE, related_name="user_resetpassword")
    reset_token = models.CharField("Password reset token",max_length=400, null= True, blank=True)
    valid_to = models.DateTimeField("Valid Till")
    
    def __str__(self):
        return f"{self.customer.id}|{self.reset_token}"
    
class Payment(models.Model):
    user_id = models.ForeignKey(UserData, on_delete=models.PROTECT, null=True)
    package_selected = models.CharField(max_length=500)
    transaction_amount = models.IntegerField()
    date_created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"User: {self.user_id} on {self.date_created}"
    
class Orders(models.Model):
    user_id = models.ForeignKey(UserData, on_delete=models.PROTECT, null=True)
    product_name = models.CharField(max_length=300)
    link = models.CharField(max_length=400)
    image_link = models.CharField(max_length=400)
    price = models.DecimalField(max_digits=60, decimal_places=2)
    quantity = models.DecimalField(max_digits=65, decimal_places=3)
    unit = models.CharField(max_length=100, blank=True, null=True)
    relative_price = models.DecimalField(max_digits=65, decimal_places=2)
    vendor = models.CharField(max_length=100, default='None')
    supplier = models.ForeignKey(
        "backend.Vendor", 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    brand = models.CharField(max_length=100, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

class Searches(models.Model):
    user_id = models.ForeignKey(UserData, on_delete=models.CASCADE, null=True)
    search = models.CharField(max_length=300)
    results = models.IntegerField()
    is_deleted = models.BooleanField(default=False)

class Scraper(models.Model):
    website = models.CharField(max_length=300)
    scraped = models.CharField(max_length=300)
    last_scraped = models.DateField()
    is_deleted = models.BooleanField(default=False)

class Products(models.Model):
    product_name = models.CharField(max_length=800)
    link = models.CharField(max_length=800)
    image_link = models.CharField(max_length=800)
    price = models.DecimalField(max_digits=60, decimal_places=2)
    relative_price = models.DecimalField(max_digits=65, decimal_places=2)
    vendor = models.CharField(max_length=100, default='None')
    brand = models.CharField(max_length=100, default='None')
    supplier = models.ForeignKey(
        "backend.Vendor",
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name="products",
    )
    scraper = models.ForeignKey(Scraper, on_delete=models.PROTECT, null=True)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.product_name}|{self.price}"
    
    @staticmethod
    def get_brands_list(qs):
        b_list= set()
        for obj in qs:
            if obj.brand:
                b_list.add(obj.brand)
        return list(b_list)
    
    @staticmethod
    def get_vendors_list():
        vlist = list(Vendor.objects.all().values_list('name', flat=True))
        return vlist

class Wishlist(models.Model):
    user_id = models.ForeignKey(UserData, on_delete=models.PROTECT, related_name="wishlists", null=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="wishlists")
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user_id.name}|{self.product}"    

class Vendor(models.Model):
    name = models.CharField("Name", max_length=120)
    phone = models.CharField('Phone', max_length=20, null=True, blank=True)
    email = models.CharField("Email", max_length=64, null=True, blank=True)
    website = models.URLField(max_length=120)
    address = models.JSONField("Address", default=dict, blank=True)
    is_active = models.BooleanField("Active", default=True)
    
    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=64)
    
    def __str__(self):
        return self.name




class XMLFile(models.Model):
    file = models.FileField(upload_to='xml_uploads/')
    filename = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename