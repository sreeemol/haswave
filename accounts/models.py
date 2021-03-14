from django.db import models
from django.utils.translation import gettext_lazy as _

from general.models import Base, Country, State, City
from accounts.models import User

from general.models import PaymentTerm
from general.currencies import currencies
from organizations.models import Organization,Branch

from phonenumber_field.modelfields import PhoneNumberField

SALUTATIONS = (
        ('', 'Select'),
        ('mr', 'Mr'),
        ('ms', 'Ms'),
        ('mrs', 'Mrs'),
    )

CLIENT_TYPE =(
    ('business','Business'),
    ('individual','Individual'),
)

PAYMENT_TERMS =(
    ('fixed','Fixed'),
    ('hourly','Hourly'),
)

class Client(Base):
    """
    Client model associated with details of a client
    """
    user = models.OneToOneField(User, null=True, related_name='client_user', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.PROTECT)
    department = models.ForeignKey('departments.Department', null=True, blank=True, on_delete=models.PROTECT)
    photo = models.ImageField(upload_to='media/client', blank=True, null=True)
    
    salutation = models.CharField(max_length=4, choices=SALUTATIONS)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    company_name = models.CharField(max_length=128, blank=True)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=20, blank=True)
    website = models.URLField(max_length=200, blank=True)
    client_type = models.CharField(max_length=20,choices=CLIENT_TYPE)
    client_display_name = models.CharField(max_length=128, null=True, blank=True)
    work_phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.first_name +" "+ self.last_name

    class Meta(Base.Meta):
        permissions = (
            ("change_client_status", "Can change client status"),
        )


class OtherDetails(models.Model):
    """
        OtherDetails model associated with other details of the client
    """
    client = models.OneToOneField(Client, on_delete=models.CASCADE)
    currency = models.CharField(max_length=4, blank=True, choices=currencies)
    payment_terms = models.CharField(max_length=20,null=True, blank=True)
    enable_portal = models.BooleanField(default=False)
    portal_language = models.CharField(max_length=128, default='en')
    facebook = models.URLField(max_length=200, blank=True)
    skype_name = models.CharField(_('Skype Name / Number'), max_length=128, blank=True)

    class Meta:
        verbose_name_plural = "OtherDetails"


class Address(models.Model):
    """
      Address model associated with Billing details of the client
    """
    client = models.OneToOneField(Client, on_delete=models.CASCADE)
    attention = models.CharField(max_length=128, blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    state = models.ForeignKey(State, on_delete=models.PROTECT, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, blank=True, null=True)
    address1 = models.TextField(blank=True)
    address2 = models.TextField(blank=True)
    pin_code = models.CharField(_('Zip Code'), max_length=20, blank=True, null=True)
    fax = models.CharField(max_length=16, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name_plural = "Address"


class ShippingAddress(models.Model):
    """
    ShippingAddress model associated with Shipping details of the client
    """
    client = models.OneToOneField(Client, on_delete=models.CASCADE)
    shipping_attention = models.CharField(max_length=128, blank=True)
    shipping_country = models.ForeignKey(Country, on_delete=models.PROTECT, blank=True, null=True)
    shipping_state = models.ForeignKey(State, on_delete=models.PROTECT, blank=True, null=True)
    shipping_city = models.ForeignKey(City, on_delete=models.PROTECT, blank=True, null=True)
    shipping_address1 = models.TextField(blank=True)
    shipping_address2 = models.TextField(blank=True)
    shipping_pin_code = models.CharField(_('Zip Code'), max_length=20, blank=True, null=True)
    shipping_fax = models.CharField(max_length=16, blank=True, null=True)
    shipping_phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name_plural = "Shipping Address"

class ContactPerson(models.Model):
    """
    ContactPerson model associated with contact details of the client
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    contactperson_salutation = models.CharField(max_length=4, choices=SALUTATIONS)
    contactperson_first_name = models.CharField(max_length=128)
    contactperson_last_name = models.CharField(max_length=128, blank=True)
    contactperson_email = models.EmailField(blank=True, null=True)
    contactperson_mobile_number = models.CharField(max_length=20, blank=True)
    contactperson_skype_name = models.CharField(max_length=20, blank=True)
    
    
class Remark(models.Model):
    """
    Remark model associated with remark details of the client
    """
    client = models.OneToOneField(Client, on_delete=models.CASCADE)
    remarks = models.TextField(blank=True)

class ClientComment(Base):
    """
    Comment model associated with comments about the client
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    comment = models.TextField()