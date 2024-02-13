import django_filters
from django.db.models import Q

from utilities.filters import MultiValueCharFilter
from .models import MetaType


class MetaTypeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    name = MultiValueCharFilter(
        lookup_expr='iexact'
    )

    vendor = django_filters.CharFilter(
        method='by_vendor',
        label='Vendor',
    )

    class Meta:
        model = MetaType
        fields = ['id', 'name', 'vendor']

    def by_vendor(self, queryset, name, value):
        if not value.strip():
            return queryset
        if ',' in value:
            q = Q()
            for _ in value.split(','):
                if _:
                    q |= Q(vendor__icontains=_)
            return queryset.filter(q)
        return queryset.filter(Q(vendor__icontains=value))

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        qs_filter = (
                Q(name__icontains=value) | Q(vendor__icontains=value)
        )
        return queryset.filter(qs_filter)
