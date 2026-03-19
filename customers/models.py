from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # 10-digit phone number as requested
    phone = models.BigIntegerField(
        unique=True,
        validators=[
            MinValueValidator(1000000000, message="Phone number must be 10 digits."),
            MaxValueValidator(9999999999, message="Phone number must be 10 digits.")
        ],
        help_text="10 digit phone number. Acts as the primary login ID."
    )
    
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField() # Mandatory
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"
