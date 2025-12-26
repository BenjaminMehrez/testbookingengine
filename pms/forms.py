from datetime import datetime
from django import forms
from django.forms import ModelForm


from .models import Booking, Customer

class RoomSearchForm(ModelForm):
    class Meta:
        model = Booking
        fields = ['checkin', 'checkout', 'guests']
        labels = {
            "guests": "Huéspedes"
        }
        widgets = {
            'checkin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control w-25'}),
            'checkout': forms.DateInput(attrs={'type': 'date', 'class': 'form-control w-25'}),
            'guests': forms.NumberInput(attrs={'type': 'number', 'min': 1, 'max': 4, 'class': 'form-control w-25'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values for checkin and checkout
        self.fields['checkin'].widget.attrs['min'] = datetime.today().strftime('%Y-%m-%d')


class CustomerForm(ModelForm):
    class Meta:
        model = Customer
        fields = "__all__"
        labels = {
            "name": "Nombre y apellido",
            "phone": "Teléfono"
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class BookingForm(ModelForm):
    class Meta:
        model = Booking
        fields = "__all__"
        widgets = {
            'checkin': forms.HiddenInput(),
            'checkout': forms.HiddenInput(),
            'guests': forms.HiddenInput()
        }


class BookingFormExcluded(ModelForm):
    class Meta:
        model = Booking
        exclude = ["customer", "room", "code"]
        widgets = {
            'checkin': forms.HiddenInput(),
            'checkout': forms.HiddenInput(),
            'guests': forms.HiddenInput(),
            'total': forms.HiddenInput(),
            'state': forms.HiddenInput(),
        }
