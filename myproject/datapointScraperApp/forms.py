from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Datapoint

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class DatapointForm(forms.ModelForm):
    class Meta:
        model = Datapoint
        fields = [
            'name',
            'url',
            'xpath',
            'data_type',
            'data_group',
            'organization',
            'status',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Datapoint Name'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'xpath': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '//div[@id="content"]'}),
            'data_type': forms.Select(attrs={'class': 'form-select'}),
            'data_group': forms.Select(attrs={'class': 'form-select'}),
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }