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
            'current_verified_data',
            'data_group',
            'organization',
            'status',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Datapoint Name'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'xpath': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '//div[@id="content"]'}),
            'data_type': forms.Select(attrs={'class': 'form-select'}),
            'current_verified_data': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Verified Data', 'rows': 3}),
            'data_group': forms.Select(attrs={'class': 'form-select'}),
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class TestXPathForm(forms.Form):
    DATA_TYPE_CHOICES = [
        ('TXT', 'Text (TXT)'),
        ('HTML', 'HTML (HTML)'),
    ]

    url = forms.URLField(
        label='URL',
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
        required=True
    )
    xpath = forms.CharField(
        label='XPath Expression',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '//h1'}),
        required=True
    )
    data_type = forms.ChoiceField(
        label='Data Type',
        choices=DATA_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        initial='TXT'
    )

class UserSettingsForm(forms.Form):
    # Column Preferences
    COLUMN_CHOICES = [
        ('0', 'Name'),
        ('1', 'Organization'),
        ('2', 'Data Group'),
        ('3', 'URL'),
        ('4', 'XPath'),
        ('5', 'Data Type'),
        ('6', 'Verified Data'),
        ('7', 'Unverified Data'),
        ('8', 'Status'),
        ('9', 'Last Updated'),
        # '10' is 'Actions', which we'll keep always visible
    ]

    columns = forms.MultipleChoiceField(
        choices=COLUMN_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        initial=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
    )

    # Theme Preferences
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]

    theme = forms.ChoiceField(
        choices=THEME_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        initial='light'
    )