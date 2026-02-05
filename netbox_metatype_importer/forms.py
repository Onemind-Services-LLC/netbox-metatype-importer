from django import forms

from netbox.forms import NetBoxModelFilterSetForm

from .models import MetaType


class MetaTypeFilterForm(NetBoxModelFilterSetForm):
    model = MetaType
    vendor = forms.CharField(required=False, label='Vendor')
