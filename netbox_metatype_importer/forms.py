from django import forms

from utilities.forms import BootstrapMixin
from .models import MetaType


class MetaTypeFilterForm(BootstrapMixin, forms.Form):
    q = forms.CharField(
        required=False,
        label='Search'
    )

    name = forms.CharField(
        required=False,
        label='Model'
    )
    vendor = forms.CharField(
        required=False,
        label='Vendor'
    )

    class Meta:
        model = MetaType
        fields = ['q', 'name', 'vendor']
