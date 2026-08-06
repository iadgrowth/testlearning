from django import forms
from django.contrib.auth.models import User
from .models import Customer, CustomerPowerlist


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'website']


class CustomerPowerlistForm(forms.ModelForm):
    class Meta:
        model = CustomerPowerlist
        fields = ['powerlist_id', 'campaign_name']


class UserCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match.")
        if User.objects.filter(username=cleaned.get('username')).exists():
            raise forms.ValidationError("That username is already taken.")
        return cleaned


class PasswordResetForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('new_password') != cleaned.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned
