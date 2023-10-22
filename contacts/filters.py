from django_filters import FilterSet
from contacts.models import Contact, AllowedField, Segment


class ContactFilter(FilterSet):
    class Meta:
        model = Contact
        fields = ['email', ]


class CustomFieldFilter(FilterSet):
    class Meta:
        model = AllowedField
        fields = ['name', 'type',]


class SegmentFilter(FilterSet):
    class Meta:
        model = Segment
        fields = ['name', 'updated_by',]


