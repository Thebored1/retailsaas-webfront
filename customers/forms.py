from django import forms
from django.db import transaction
from .models import Customer
from django.contrib.auth.models import User

PHONE_INPUT_ATTRS = {
    "type": "tel",
    "inputmode": "numeric",
    "maxlength": "10",
    "pattern": "[0-9]{10}",
    "autocomplete": "tel",
    "title": "Enter a 10-digit phone number",
    "oninput": "this.value=this.value.replace(/\\D/g,'').slice(0,10)",
}


def _normalize_phone(value):
    phone = str(value).strip()
    if not phone.isdigit() or len(phone) != 10:
        raise forms.ValidationError("Phone number must be exactly 10 digits.")
    return int(phone)


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Customer
        fields = ['phone', 'name', 'email', 'address']
        labels = {
            'phone': 'Phone Number',
        }
        widgets = {
            'phone': forms.TextInput(attrs={**PHONE_INPUT_ATTRS, 'placeholder': '10-digit phone number'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        phone = _normalize_phone(phone)
        if Customer.objects.filter(phone=phone).exists():
            raise forms.ValidationError("A customer with this phone number already exists.")
        if User.objects.filter(username=str(phone)).exists():
            raise forms.ValidationError("An account with this phone number already exists.")
        return phone

    def save(self, commit=True):
        customer = super().save(commit=False)
        customer.name = customer.name.title()

        if not commit:
            return customer

        with transaction.atomic():
            # Create the underlying Django User where username is the phone number
            user = User.objects.create_user(
                username=str(self.cleaned_data['phone']),
                password=self.cleaned_data['password'],
                first_name=customer.name.split()[0],  # use the newly title-cased name
                email=self.cleaned_data.get('email', '')
            )
            customer.user = user
            customer.save()
        return customer

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['phone', 'name', 'email', 'address']
        labels = {
            'phone': 'Phone Number',
        }
        widgets = {
            'phone': forms.TextInput(attrs={**PHONE_INPUT_ATTRS, 'placeholder': '10-digit phone number'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        phone = _normalize_phone(phone)
        # Ensure we do not collide with another user's phone
        if User.objects.filter(username=str(phone)).exclude(id=self.instance.user_id).exists():
            raise forms.ValidationError("An account with this phone number already exists.")
        return phone

    def save(self, commit=True):
        customer = super().save(commit=False)
        customer.name = customer.name.title()
        
        if customer.user:
            customer.user.username = str(self.cleaned_data['phone'])
            customer.user.first_name = customer.name.split()[0]
            customer.user.email = self.cleaned_data.get('email', '')
            if commit:
                customer.user.save()
                
        if commit:
            customer.save()
        return customer


class SignInForm(forms.Form):
    phone = forms.IntegerField(
        min_value=1000000000, 
        max_value=9999999999, 
        label="Phone Number",
        widget=forms.TextInput(attrs={**PHONE_INPUT_ATTRS, 'placeholder': 'Enter your registered phone number'})
    )
    password = forms.CharField(widget=forms.PasswordInput)
