from django import forms

from contacts.models import Contact, AllowedField, Segment, Group, Filter


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        exclude = ['belongs_to', 'fields', 'updated_by']

    def __init__(self, *args, **kwargs):
        """Override __init__ to declare dynamically the custom fields."""
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        allowed_fields = (
            AllowedField.objects.filter(belongs_to=self.request.user.company)
            .values('name', 'type')
        )
        fields = {}
        for field in allowed_fields:
            match field['type']:
                case 'str':
                    fields[f"fields__{field['name']}"] = forms.CharField(required=False)
                case 'number':
                    fields[f"fields__{field['name']}"] = forms.IntegerField(required=False, widget=forms.NumberInput())
                case 'date':
                    fields[f"fields__{field['name']}"] = forms.DateField(required=False)
                case 'bool':
                    fields[f"fields__{field['name']}"] = forms.BooleanField(required=False, widget=forms.CheckboxInput())
        self.fields.update(fields)


class CustomFieldForm(forms.ModelForm):
    class Meta:
        model = AllowedField
        exclude = ['belongs_to']

    def as_search_filters(self):
        """Override as_p to add the form."""
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


class SegmentForm(forms.ModelForm):
    description = forms.CharField(required=False)

    class Meta:
        model = Segment
        exclude = ['belongs_to', 'members', 'updated_by', 'filters']

    def __init__(self, *args, **kwargs):
        """Override __init__ to declare dynamically the filters."""
        if kwargs.get('request'):
            self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = ['filters', 'belongs_to', 'segment']


class FilterForm(forms.ModelForm):
    class Meta:
        model = Filter
        exclude = ['belongs_to']
