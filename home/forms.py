from django import forms
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Contact, CateringEnquiry, Review, Newsletter

phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)


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
                'class': 'form-control', 'placeholder': 'Phone Number'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Your Message',
                'rows': 4
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        if '<script>' in name.lower() or 'href=' in name.lower():
            raise forms.ValidationError("Invalid characters in name.")
        return name


class CateringEnquiryForm(forms.ModelForm):
    class Meta:
        model = CateringEnquiry
        fields = ['name', 'phone', 'event_type', 'event_date', 'guests', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Enter your name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Enter phone number'
            }),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'event_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'guests': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'Approximate guest count'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Tell us about flavours, theme, timing, etc.',
                'rows': 4
            }),
        }


class OrderCustomerForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'})
    )
    phone = forms.CharField(
        max_length=17, validators=[phone_validator],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
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
