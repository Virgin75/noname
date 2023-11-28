from django.forms import IntegerField, ModelForm
from django_filters import NumberFilter


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
