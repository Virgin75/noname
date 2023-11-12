from django_filters import FilterSet, CharFilter, MultipleChoiceFilter, OrderingFilter, ChoiceFilter

from contacts.forms import CustomFieldForm
from contacts.models import Contact, AllowedField, Segment
from django.forms import CheckboxSelectMultiple


class ContactFilter(FilterSet):
    class Meta:
        model = Contact
        fields = ['email', ]


class CustomFieldFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')
    name.field.group = "search"
    type = ChoiceFilter(choices=AllowedField.ALLOWED_TYPES, lookup_expr='exact')
    type.field.group = "filters"
    order_by = OrderingFilter(fields=[('name', 'name'), ('type', 'type')])
    order_by.field.group = "sort"

    class Meta:
        model = AllowedField
        fields = ['name', 'type',]
        form = CustomFieldForm


class SegmentFilter(FilterSet):
    class Meta:
        model = Segment
        fields = ['name', 'updated_by',]


