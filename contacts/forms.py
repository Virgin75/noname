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
        self.fields.update({
            'fields__passion': forms.CharField(widget=forms.Textarea()),
        })
