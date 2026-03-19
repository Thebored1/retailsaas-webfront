from django import forms
from .models import Customer
from django.contrib.auth.models import User

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Customer
        fields = ['phone', 'name', 'email', 'address']
        widgets = {
            'phone': forms.TextInput(attrs={
                'type': 'tel', 
                'maxlength': '10',
                'pattern': '[0-9]{10}',
                'title': 'Must be exactly 10 digits'
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(username=str(phone)).exists():
            raise forms.ValidationError("An account with this phone number already exists.")
        return phone

    def save(self, commit=True):
        customer = super().save(commit=False)
        customer.name = customer.name.title()
        
        # Create the underlying Django User where username is the phone number
        user = User.objects.create_user(
            username=str(self.cleaned_data['phone']),
            password=self.cleaned_data['password'],
            first_name=customer.name.split()[0], # use the newly title-cased name
            email=self.cleaned_data.get('email', '')
        )
        customer.user = user
        if commit:
            customer.save()
        return customer

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['phone', 'name', 'email', 'address']
        widgets = {
            'phone': forms.TextInput(attrs={
                'type': 'tel', 
                'maxlength': '10',
                'pattern': '[0-9]{10}',
                'title': 'Must be exactly 10 digits'
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
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
        label="10-Digit Phone Number",
        widget=forms.TextInput(attrs={
            'type': 'tel', 
            'maxlength': '10',
            'pattern': '[0-9]{10}',
            'title': 'Must be exactly 10 digits'
        })
    )
    password = forms.CharField(widget=forms.PasswordInput)
