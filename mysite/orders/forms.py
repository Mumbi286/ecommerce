from django import forms
from .models import Address


def normalize_kenyan_phone(number):
    """Converting 0712345678 / 0112345678 into the +254 format before saving,
    so every phone number in the database looks the same."""
    number = number.strip().replace(" ", "")
    if number.startswith("0"):
        number = "+254" + number[1:]
    return number


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ['user']
        labels = {
            'phone': 'Phone number',
            'phone_alt': 'Alternative phone (optional)',
            'delivery_details': 'Delivery details',
            'city': 'City / Town',
            'county': 'County',
            'postal_code': 'Postal code',
        }
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'e.g. Jane Wanjiku'}),
            'phone': forms.TextInput(attrs={'placeholder': 'e.g. +254712345678'}),
            'phone_alt': forms.TextInput(attrs={'placeholder': 'e.g. 0712345678 (optional)'}),
            'delivery_details': forms.TextInput(attrs={'placeholder': 'Estate, building, street, house no.'}),
            'city': forms.TextInput(attrs={'placeholder': 'e.g. Nairobi'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'e.g. 00100'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded'
            })

    def clean_phone(self):
        return normalize_kenyan_phone(self.cleaned_data['phone'])

    def clean_phone_alt(self):
        phone_alt = self.cleaned_data.get('phone_alt', '')
        if phone_alt:
            return normalize_kenyan_phone(phone_alt)
        return phone_alt
