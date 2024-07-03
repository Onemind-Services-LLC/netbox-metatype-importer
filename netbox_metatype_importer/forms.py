from django import forms

from .models import MetaType


class MetaTypeFilterForm(forms.Form):
    q = forms.CharField(required=False, label='Name')

    vendor = forms.CharField(required=False, label='Vendor')

    class Meta:
        model = MetaType
        fields = ['q', 'vendor']
