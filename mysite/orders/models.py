from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from myapp.models import Product

# validators that make the address fields 
full_name_validator = RegexValidator(
    r"^[A-Za-z]+(?:['-][A-Za-z]+)*(?: [A-Za-z]+(?:['-][A-Za-z]+)*)+$",
    "Enter your full name (first and last name), letters only.",
)
kenyan_phone_validator = RegexValidator(
    r"^(?:\+254|0)(?:7|1)\d{8}$",
    "Enter a valid Kenyan phone number e.g. +254712345678 or 0712345678.",
)
city_validator = RegexValidator(
    r"^[A-Za-z]+(?:[' -][A-Za-z]+)*$",
    "Enter a valid city or town name, letters only.",
)
postal_code_validator = RegexValidator(
    r"^\d{5}$",
    "Kenyan postal codes are exactly 5 digits e.g. 00100.",
)

# the 47 counties of Kenya, dropdown choices
KENYAN_COUNTIES = [
    "Baringo", "Bomet", "Bungoma", "Busia", "Elgeyo-Marakwet", "Embu",
    "Garissa", "Homa Bay", "Isiolo", "Kajiado", "Kakamega", "Kericho",
    "Kiambu", "Kilifi", "Kirinyaga", "Kisii", "Kisumu", "Kitui", "Kwale",
    "Laikipia", "Lamu", "Machakos", "Makueni", "Mandera", "Marsabit",
    "Meru", "Migori", "Mombasa", "Murang'a", "Nairobi", "Nakuru", "Nandi",
    "Narok", "Nyamira", "Nyandarua", "Nyeri", "Samburu", "Siaya",
    "Taita-Taveta", "Tana River", "Tharaka-Nithi", "Trans Nzoia",
    "Turkana", "Uasin Gishu", "Vihiga", "Wajir", "West Pokot",
]
COUNTY_CHOICES = [(county, county) for county in KENYAN_COUNTIES]


# Create your models here.
class Address(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100,validators=[full_name_validator])
    phone = models.CharField(max_length=13,validators=[kenyan_phone_validator])
    # optional second number in case the main one is unreachable
    phone_alt = models.CharField(max_length=13,blank=True,default="",validators=[kenyan_phone_validator])
    # estate / building / street / house number — what the courier reads
    delivery_details = models.CharField(max_length=255)
    city = models.CharField(max_length=100,validators=[city_validator])
    county = models.CharField(max_length=30,choices=COUNTY_CHOICES)
    postal_code = models.CharField(max_length=5,validators=[postal_code_validator])
    # deliveries are Kenya-only, so this is fixed and not shown on the form
    country = models.CharField(max_length=100,default="Kenya",editable=False)

# when a user places an order
class Order(models.Model):
    # null=True allows guest orders that are not linked to any account
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    total_amount = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


# information on the items that the user has ordered
class OrderItem(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name="items")
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    # a derived field that the user should always have the total with them
    @property
    def total_price(self):
        return self.product.price * self.quantity

