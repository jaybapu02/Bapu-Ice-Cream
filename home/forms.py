import re

from django import forms
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator, ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Contact, CateringEnquiry, Review, Newsletter


def normalize_phone(value):
    """
    Strip formatting, normalize to +91 for Indian numbers,
    then validate. Returns the normalized number or raises ValidationError.
    """
    cleaned = re.sub(r'[\s\-\(\)\.]', '', value)

    if not cleaned.startswith('+'):
        if cleaned.startswith('0'):
            if len(cleaned) == 11 and cleaned[1].isdigit():
                cleaned = '+91' + cleaned[1:]
        elif cleaned.startswith('91') and len(cleaned) == 12:
            cleaned = '+' + cleaned
        elif len(cleaned) == 10 and cleaned[0] in '6789':
            cleaned = '+91' + cleaned

    if cleaned.startswith('+91'):
        if not re.match(r'^\+91[6-9]\d{9}$', cleaned):
            raise ValidationError(
                "Enter a valid Indian mobile number: 10 digits starting with 6-9 "
                "(+91 prefix optional, e.g. +919876543210 or 9876543210)."
            )
    elif cleaned.startswith('+'):
        if not re.match(r'^\+\d{10,15}$', cleaned):
            raise ValidationError(
                "International numbers must start with + followed by 10–15 digits "
                "(e.g. +14155552671)."
            )
    else:
        raise ValidationError("Enter a valid phone number with country code.")

    return cleaned


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'Your Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. +919876543210',
                'type': 'tel'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Your Message',
                'rows': 4
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        if len(name) < 2:
            raise forms.ValidationError("Name must be at least 2 characters.")
        if re.search(r'<[^>]*>|href\s*=|javascript\s*:', name, re.I):
            raise forms.ValidationError("Invalid characters in name.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        return normalize_phone(phone)

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if not message:
            raise forms.ValidationError("Message is required.")
        if len(message) < 10:
            raise forms.ValidationError("Message must be at least 10 characters.")
        return message


class CateringEnquiryForm(forms.ModelForm):
    class Meta:
        model = CateringEnquiry
        fields = [
            'name', 'phone', 'email', 'event_type', 'event_date',
            'venue', 'guests', 'catering_package', 'budget',
            'special_requirements', 'message', 'reference_image',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Your full name',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. +919876543210',
                'type': 'tel', 'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'your@email.com',
            }),
            'event_type': forms.Select(attrs={
                'class': 'form-select', 'required': True,
            }),
            'event_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'venue': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Venue name or address',
            }),
            'guests': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'Approx. number of guests',
                'min': 1,
            }),
            'catering_package': forms.Select(attrs={
                'class': 'form-select',
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'Approx. budget in INR',
                'min': 0, 'step': '100',
            }),
            'special_requirements': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Dietary restrictions, allergies, preferred flavours, etc.',
                'rows': 3,
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Any additional details or requests...',
                'rows': 3,
            }),
            'reference_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        if len(name) < 2:
            raise forms.ValidationError("Name must be at least 2 characters.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        return normalize_phone(phone)

    def clean_event_date(self):
        date = self.cleaned_data.get('event_date')
        if date:
            from datetime import date as dt_date
            if date < dt_date.today():
                raise forms.ValidationError("Event date cannot be in the past.")
        return date

    def clean_guests(self):
        guests = self.cleaned_data.get('guests')
        if guests and guests > 50000:
            raise forms.ValidationError("Please contact us directly for events with 50,000+ guests.")
        return guests

    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget and budget > 99999999:
            raise forms.ValidationError("Please enter a realistic budget amount.")
        return budget

    def clean_reference_image(self):
        img = self.cleaned_data.get('reference_image')
        if img:
            if img.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image must be less than 5 MB.")
            allowed = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
            if hasattr(img, 'content_type') and img.content_type not in allowed:
                raise forms.ValidationError("Only JPG, PNG, WebP, or GIF images are allowed.")
        return img


class OrderCustomerForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'})
    )
    phone = forms.CharField(
        max_length=17,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'e.g. +919876543210',
            'type': 'tel'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'placeholder': 'Delivery Address', 'rows': 2
        })
    )
    delivery_type = forms.ChoiceField(
        choices=[('Home Delivery', 'Home Delivery'), ('Takeaway', 'Takeaway')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    payment_mode = forms.ChoiceField(
        choices=[('Cash on Delivery', 'Cash on Delivery'), ('UPI', 'UPI'), ('Card', 'Card')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        return normalize_phone(phone)

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        if re.search(r'<[^>]*>|href\s*=|javascript\s*:', name, re.I):
            raise forms.ValidationError("Invalid characters in name.")
        return name


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['name', 'email', 'rating', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'Your Email'
            }),
            'rating': forms.Select(attrs={'class': 'form-select'}, choices=[
                (5, '★★★★★ (5)'),
                (4, '★★★★☆ (4)'),
                (3, '★★★☆☆ (3)'),
                (2, '★★☆☆☆ (2)'),
                (1, '★☆☆☆☆ (1)'),
            ]),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Share your experience...',
                'rows': 3
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        if re.search(r'<[^>]*>|href\s*=|javascript\s*:', name, re.I):
            raise forms.ValidationError("Invalid characters in name.")
        return name


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'Your Email Address'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Newsletter.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError("You are already subscribed!")
        return email


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Confirm Password'
        })
