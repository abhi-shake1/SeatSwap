from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import SeatListing, UserProfile


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    upi_id = forms.CharField(max_length=100, required=False, help_text="Enter your UPI ID for receiving payments")
    
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'upi_id', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control'})
        self.fields['upi_id'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class SeatListingForm(forms.ModelForm):
    class Meta:
        model = SeatListing
        fields = ['pnr_number', 'seat_type', 'seat_number', 'coach_number', 'price', 'description']
        widgets = {
            'pnr_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter 10-digit PNR number'
            }),
            'seat_type': forms.Select(attrs={'class': 'form-control'}),
            'seat_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 45'
            }),
            'coach_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., S1'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter price in INR'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional details about the seat...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pnr_number'].help_text = "Enter your 10-digit PNR number"
        self.fields['price'].help_text = "Enter the amount you want to charge for the seat exchange"
        self.fields['description'].required = False


class PNRForm(forms.Form):
    pnr_number = forms.CharField(
        max_length=10,
        min_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 10-digit PNR number'
        })
    )
    
    def clean_pnr_number(self):
        pnr = self.cleaned_data['pnr_number']
        if not pnr.isdigit():
            raise forms.ValidationError("PNR number must contain only digits")
        return pnr


class SeatSearchForm(forms.Form):
    source_station = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter source station'
        })
    )
    destination_station = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter destination station'
        })
    )
    journey_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class PNRLoginForm(forms.Form):
    """Form for PNR-based login after authentication"""
    pnr_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current journey PNR',
            'pattern': '[0-9]{10}',
            'title': 'Please enter a 10-digit PNR number'
        })
    )
    
    def clean_pnr_number(self):
        pnr = self.cleaned_data['pnr_number']
        if not pnr.isdigit() or len(pnr) != 10:
            raise forms.ValidationError("PNR number must be exactly 10 digits")
        return pnr
