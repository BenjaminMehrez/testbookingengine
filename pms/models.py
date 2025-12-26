from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone

# Create your models here.

# Validator for phone
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="El número debe tener el formato: '+999999999'. Hasta 15 dígitos."
)

class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    # Apply phone validator
    phone = models.CharField(validators=[phone_regex], max_length=50)  # TODO:ADD REGEX FOR PHONE VALIDATION

    def __str__(self):
        return self.name


class Room_type(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()
    max_guests = models.IntegerField()

    def __str__(self):
        return self.name


class Room(models.Model):
    room_type = models.ForeignKey(Room_type, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class Booking(models.Model):
    NEW = 'NEW'
    DELETED = 'DEL'
    STATE_CHOICES = [
        (NEW, 'Nueva'),
        (DELETED, 'Cancelada'),
    ]
    state = models.CharField(
        max_length=3,
        choices=STATE_CHOICES,
        default=NEW,
    )
    checkin = models.DateField()
    checkout = models.DateField()
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    guests = models.IntegerField()
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    total = models.FloatField()
    code = models.CharField(max_length=8)
    created = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Validate dates
        if self.checkin and self.checkout:
            if self.checkin >= self.checkout:
                raise ValidationError('La fecha de salida debe ser posterior a la de entrada.')
        
        # Validate that it is not in the past
        if not self.pk and self.checkin and self.checkin < timezone.now().date():
            raise ValidationError('No puedes reservar en el pasado.')

    def save(self, *args, **kwargs):
        self.full_clean()  # Validate before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code
