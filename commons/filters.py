from django.forms import ModelForm


class FilteredModelForm(ModelForm):
    def as_search_filters(self):
        """Override as_table to add the form specific html."""
        return self.as_table()

    def _bound_items(self):
        """Yield (name, bf) pairs, where bf is a BoundField object."""
        for name, value in self.fields.items():
            bound_item = self[name]
            try:
                bound_item.group = value.group
            except AttributeError:
                pass
            yield name, bound_item
