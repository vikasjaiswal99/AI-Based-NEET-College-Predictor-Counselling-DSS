"""apps/accounts/forms.py"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

CATEGORY_CHOICES = [
    ('GEN', 'General'), ('OBC', 'OBC'), ('SC', 'SC'), ('ST', 'ST'), ('EWS', 'EWS'),
]

STATE_CHOICES = [
    ('', 'Select State'),
    ('Andhra Pradesh', 'Andhra Pradesh'), ('Assam', 'Assam'), ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'), ('Delhi', 'Delhi'), ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'), ('Haryana', 'Haryana'), ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jammu And Kashmir', 'Jammu & Kashmir'), ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'), ('Kerala', 'Kerala'), ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'), ('Manipur', 'Manipur'), ('Meghalaya', 'Meghalaya'),
    ('Nagaland', 'Nagaland'), ('Odisha', 'Odisha'), ('Puducherry', 'Puducherry'),
    ('Punjab', 'Punjab'), ('Rajasthan', 'Rajasthan'), ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'), ('Tripura', 'Tripura'), ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'), ('West Bengal', 'West Bengal'),
]

_WIDGET = lambda placeholder: forms.TextInput(attrs={'class': 'form-control', 'placeholder': placeholder})
_SELECT = lambda: forms.Select(attrs={'class': 'form-select'})
_EMAIL  = lambda placeholder: forms.EmailInput(attrs={'class': 'form-control', 'placeholder': placeholder})
_PASS   = lambda placeholder: forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': placeholder})


class LoginForm(forms.Form):
    email    = forms.EmailField(widget=_EMAIL('you@example.com'))
    password = forms.CharField(widget=_PASS('Your password'))


class RegisterForm(forms.Form):
    first_name       = forms.CharField(max_length=60, widget=_WIDGET('First name'))
    last_name        = forms.CharField(max_length=60, widget=_WIDGET('Last name'))
    email            = forms.EmailField(widget=_EMAIL('you@example.com'))
    category         = forms.ChoiceField(choices=CATEGORY_CHOICES, widget=_SELECT())
    state_of_domicile= forms.ChoiceField(choices=STATE_CHOICES, required=False, widget=_SELECT())
    neet_rank        = forms.IntegerField(required=False, min_value=1,
                                          widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 45000'}))
    neet_score       = forms.IntegerField(required=False, min_value=0, max_value=720,
                                          widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0–720'}))
    password         = forms.CharField(widget=_PASS('Min 8 characters'), validators=[validate_password])
    confirm_password = forms.CharField(widget=_PASS('Repeat password'))

    def clean(self):
        data = super().clean()
        if data.get('password') != data.get('confirm_password'):
            raise forms.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email
