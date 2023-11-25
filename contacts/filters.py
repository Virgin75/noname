import operator

from django_filters import CharFilter, ChoiceFilter, NumberFilter, FilterSet, OrderingFilter, BooleanFilter, TypedChoiceFilter
from django import forms
from django.db.models import Q
from functools import reduce
from commons.fields import SearchInput
from commons.filters import IntegerFilter
from contacts.forms import ContactForm, ContactFormFilters, CustomFieldForm
from contacts.models import AllowedField, Contact, Segment


class ContactFilter(FilterSet):
    search = CharFilter(method="filter_search", widget=SearchInput(attrs={"placeholder": "Search..."}))
    search.field.group = "search"
    is_unsubscribed = ChoiceFilter(choices=((True, "Yes"), (False, "No")), lookup_expr="exact", empty_label="------")
    is_unsubscribed.field.group = "filters"
    order_by = OrderingFilter(fields=[("email", "email"), ("created_at", "created_at"), ("updated_at", "updated_at")])
    order_by.field.group = "sort"

    class Meta:
        model = Contact
        fields = [
            "email",
        ]
        form = ContactFormFilters

    def __init__(self, *args, **kwargs):
        """Override __init__ to declare dynamically the custom fields."""
        super().__init__(*args, **kwargs)
        allowed_fields = AllowedField.objects.filter(belongs_to=self.request.user.company).values("name", "type")
        fields = {}
        self.search_fields = []
        for field in allowed_fields:
            match field["type"]:
                case "str":
                    self.search_fields.append(f"fields__{field['name']}")
                case "number":
                    fields[f"{field['name']}"] = IntegerFilter(
                        field_name=f"fields__{field['name']}",
                        lookup_expr="exact",
                        widget=forms.NumberInput(attrs={"placeholder": f'Type exact {field["name"]}...'}),
                    )
                    fields[f"{field['name']}"].field.group = "filters"
                case "date":
                    fields[f"{field['name']}"] = CharFilter(
                        field_name=f"fields__{field['name']}",
                        lookup_expr="icontains",
                        widget=SearchInput(attrs={"placeholder": f'Search {field["name"]}...'}),
                    )
                    fields[f"{field['name']}"].field.group = "filters"
                case "bool":
                    fields[f"{field['name']}"] = TypedChoiceFilter(
                        choices=((None, "-----"), (True, "Yes"), (False, "No")),
                        coerce=lambda x: x == "True",
                        field_name=f"fields__{field['name']}",
                        lookup_expr="exact",
                    )
                    fields[f"{field['name']}"].field.group = "filters"
        self.filters.update(fields)

    def filter_search(self, queryset, name, value):
        """Allow filtering on email with icontains without being blocked by Email field validation."""
        if value:
            search_fields = [Q(**{f"{field}__icontains": value}) for field in self.search_fields]
            search_fields.append(Q(email__icontains=value))
            return queryset.filter(reduce(operator.or_, search_fields)).distinct()
        return queryset

    @property
    def form(self):
        """Override 'form' property to pass the request to the Form."""
        if not hasattr(self, "_form"):
            Form = self.get_form_class()
            if self.is_bound:
                self._form = Form(self.data, prefix=self.form_prefix, request=self.request)
            else:
                self._form = Form(prefix=self.form_prefix, request=self.request)
        return self._form


class CustomFieldFilter(FilterSet):
    name = CharFilter(lookup_expr="icontains", widget=SearchInput(attrs={"placeholder": "Search..."}))
    name.field.group = "search"
    type = ChoiceFilter(choices=AllowedField.ALLOWED_TYPES, lookup_expr="exact")
    type.field.group = "filters"
    order_by = OrderingFilter(fields=[("name", "name"), ("type", "type")])
    order_by.field.group = "sort"

    class Meta:
        model = AllowedField
        fields = [
            "name",
            "type",
        ]
        form = CustomFieldForm


class SegmentFilter(FilterSet):
    class Meta:
        model = Segment
        fields = [
            "name",
            "updated_by",
        ]
