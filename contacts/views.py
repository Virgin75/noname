from django.urls import reverse_lazy

from commons.views import OrderingMixin
from contacts.forms import ContactForm, CustomFieldForm
from contacts.models import Contact, AllowedField
from users.forms import CompanyForm
from django.views.generic.edit import CreateView, FormView, BaseUpdateView, UpdateView
from django.views.generic.list import ListView
from django.db.models.fields.json import KT
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from contacts.filters import ContactFilter, CustomFieldFilter


class CreateContact(SuccessMessageMixin, LoginRequiredMixin, FormView):
    """View used to create a new contact."""
    template_name = 'contacts/create_contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contacts:list_contacts')
    success_message = 'Contact created successfully.'

    def form_valid(self, form):
        contact = form.save(commit=False)
        contact.belongs_to = self.request.user.company
        contact.updated_by = self.request.user
        custom_fields = {}
        for k, v in form.cleaned_data.items():
            if k.startswith('fields__'):
                custom_fields[k[8:]] = v
        contact.fields = custom_fields
        contact.save()
        print(vars(contact))
        return super().form_valid(form)

    def get_form_kwargs(self):
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


class ListCustomField(SuccessMessageMixin, LoginRequiredMixin, ListView):
    template_name = 'contacts/list_custom_fields.html'

    def get_queryset(self):
        return AllowedField.objects.filter(belongs_to=self.request.user.company)

    def get_context_data(self, **kwargs):
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
        contact = form.save(commit=False)
        contact.belongs_to = self.request.user.company
        contact.save()
        return super().form_valid(form)

