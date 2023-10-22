from django import forms

from contacts.models import Contact, AllowedField


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
