from django.contrib.auth.models import User
from customers.models import Customer
import random

admin = User.objects.filter(is_superuser=True).first()
if admin:
    if not hasattr(admin, 'customer'):
        Customer.objects.create(
            user=admin,
            phone='9999999999',
            name='Store Admin',
            email=admin.email,
        )
        print("Successfully created a Customer profile for the Admin user.")
    else:
        print("Admin already has a customer profile.")
else:
    print("No superuser found in the database.")
