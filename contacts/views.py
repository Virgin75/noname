from commons.views import OrderingMixin
from contacts.models import Contact, AllowedField
from users.forms import CompanyForm
from django.views.generic.edit import CreateView, FormView, BaseUpdateView, UpdateView
from django.views.generic.list import ListView
from django.db.models.fields.json import KT
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from contacts.filters import ContactFilter


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
