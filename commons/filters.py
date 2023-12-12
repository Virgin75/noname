from django.forms import IntegerField, ModelForm
from django_filters import (
    CharFilter,
    ChoiceFilter,
    FilterSet,
    NumberFilter,
    OrderingFilter,
)

from commons.fields import SearchInput
from commons.models import ExportLog


class FilteredModelForm(ModelForm):
    def as_search_filters(self):
        """Override as_table to add the form specific html."""
        return self.as_table()

    def _bound_items(self):
        """Yield (name, bf) pairs, where bf is a BoundField object."""
        for name, value in self.fields.items():
            bound_item = self[name]
            try:
                bound_item.cols = getattr(value, "cols", 1)
                bound_item.group = getattr(value, "group", None)
            except AttributeError:
                pass
            yield name, bound_item


class IntegerFilter(NumberFilter):
    """Override default DecimalField to IntegerField."""

    field_class = IntegerField


class ExportForm(FilteredModelForm):
    class Meta:
        model = ExportLog
        exclude = ["belongs_to"]


class ExportFilter(FilterSet):
    file_name = CharFilter(lookup_expr="icontains", widget=SearchInput(attrs={"placeholder": "Search..."}))
    file_name.field.group = "search"
    status = ChoiceFilter(choices=ExportLog.STATUS, lookup_expr="exact")
    status.field.group = "filters"
    order_by = OrderingFilter(fields=[("id", "Creation date"), ("type", "Type"), ("file_name", "File name")])
    order_by.field.group = "sort"

    class Meta:
        model = ExportLog
        fields = ["file_name", "type", "status", "total_rows", "total_columns", "user"]
        form = ExportForm
