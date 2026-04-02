from django import forms
from django.core.validators import RegexValidator
from .models import Contact, CateringEnquiry, Order
import re
from django.core.exceptions import ValidationError

# Validator for 10-digit Indian phone numbers or general formats
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

class ContactForm(forms.ModelForm):
    phone = forms.CharField(validators=[phone_validator])
    
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'message']
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Basic sanitization
        if "<script>" in name.lower() or "href=" in name.lower():
            raise ValidationError("Invalid characters in name.")
        return name

class CateringEnquiryForm(forms.ModelForm):
    phone = forms.CharField(validators=[phone_validator])
    
    class Meta:
        model = CateringEnquiry
        fields = ['name', 'phone', 'event_type', 'event_date', 'guests', 'message']
        
    def clean_guests(self):
        guests = self.cleaned_data.get('guests')
        if guests is not None and guests <= 0:
            raise ValidationError("Number of guests must be a positive integer.")
        return guests

class OrderCustomerForm(forms.ModelForm):
    phone = forms.CharField(validators=[phone_validator])
    
    class Meta:
        model = Order
        fields = ['name', 'phone', 'address', 'delivery_type', 'payment_mode']
