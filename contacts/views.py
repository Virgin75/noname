import datetime

from django.urls import reverse_lazy

from commons.views import OrderingMixin
from contacts.forms import ContactForm, CustomFieldForm
from contacts.models import Contact, AllowedField
from django.views.generic.edit import CreateView, FormView, BaseUpdateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.db.models.fields.json import KT
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from contacts.filters import ContactFilter, CustomFieldFilter


class CreateContact(SuccessMessageMixin, LoginRequiredMixin, FormView):
    """View used to create a new Contact with its custom fields values."""
    template_name = 'contacts/create_contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contacts:list_contacts')
    success_message = 'Contact created successfully.'

    def form_valid(self, form):
        """Override 'form_valid()' to update the user JSONField() accordingly."""
        contact = form.save(commit=False)
        contact.belongs_to = self.request.user.company
        contact.updated_by = self.request.user
        custom_fields = {}
        for k, v in form.cleaned_data.items():
            if k.startswith('fields__'):
                if isinstance(v, datetime.date):
                    v = v.strftime('%Y-%m-%d')
                custom_fields[k[8:]] = v
        contact.fields = custom_fields
        contact.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        """Override 'get_form_kwargs()' to pass the request data to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class ListContact(SuccessMessageMixin, LoginRequiredMixin, OrderingMixin, ListView):
    template_name = 'contacts/list_contacts.html'
    paginate_by = 20
    ordering_fields = ['id', 'email']

    def get_queryset(self):
        fields = AllowedField.objects.filter(belongs_to=self.request.user.company).values_list('name', flat=True)
        annotations = {field: KT(f'fields__{field}') for field in fields}
        return (
            Contact.objects.filter(belongs_to=self.request.user.company)
            .annotate(**annotations)
            .values('id', 'email', *fields)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = ['id', 'email'] + list(AllowedField.objects.filter(belongs_to=self.request.user.company).values_list('name', flat=True))
        context['filter'] = ContactFilter(self.request.GET, queryset=self.get_queryset())
        return context


class UpdateContactView(SuccessMessageMixin, UpdateView, LoginRequiredMixin):
    """View used to update a Contact."""
    template_name = 'contacts/contact_details.html'
    model = Contact
    success_message = "Contact updated successfully."
    success_url = reverse_lazy('contacts:list_contacts')
    form_class = ContactForm

    def get_form_kwargs(self):
        """Override 'get_form_kwargs()' to pass the request data to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        """Override 'form_valid()' to update the user JSONField() accordingly."""
        contact = form.save(commit=False)
        contact.updated_by = self.request.user
        custom_fields = {}
        for k, v in form.cleaned_data.items():
            if k.startswith('fields__'):
                if isinstance(v, datetime.date):
                    v = v.strftime('%Y-%m-%d')
                custom_fields[k[8:]] = v
        contact.fields = custom_fields
        contact.save()
        return super().form_valid(form)


class DeleteContact(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    """View used to delete a Contact."""
    template_name = 'contacts/delete_contact.html'
    model = Contact
    success_url = reverse_lazy('contacts:list_contacts')
    success_message = 'Contact deleted successfully.'


class ListCustomField(SuccessMessageMixin, LoginRequiredMixin, ListView):
    template_name = 'contacts/list_custom_fields.html'

    def get_queryset(self):
        """Filter Custom fields with the user's Company."""
        return AllowedField.objects.filter(belongs_to=self.request.user.company)

    def get_context_data(self, **kwargs):
        """Pass extra data to the template: fields names and filtered queryset."""
        context = super().get_context_data(**kwargs)
        context['fields'] = ['id', 'Field name', 'Field type']
        context['filter'] = CustomFieldFilter(self.request.GET, queryset=self.get_queryset())
        return context


class CreateCustomField(SuccessMessageMixin, LoginRequiredMixin, FormView):
    """View used to create a new custom field."""
    template_name = 'contacts/create_custom_field.html'
    form_class = CustomFieldForm
    success_url = reverse_lazy('contacts:list_custom_fields')
    success_message = 'Field created successfully.'

    def form_valid(self, form):
        """Override 'form_valid()' to update 'belongs_to' field."""
        contact = form.save(commit=False)
        contact.belongs_to = self.request.user.company
        contact.save()
        return super().form_valid(form)


class DeleteCustomField(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    """View used to delete a custom field."""
    template_name = 'contacts/delete_custom_field.html'
    model = AllowedField
    success_url = reverse_lazy('contacts:list_custom_fields')
    success_message = 'Field deleted successfully.'

