import datetime

from django.urls import reverse_lazy
from django.template import Template

from commons.views import OrderingMixin
from contacts.forms import ContactForm, CustomFieldForm, SegmentForm, GroupForm, FilterForm
from contacts.models import Contact, AllowedField, Segment, Group, Filter
from django.views.generic.edit import CreateView, FormView, BaseUpdateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models.fields.json import KT
from django.core.paginator import Paginator
from django.template.loader import get_template
from django.contrib import messages

from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.response import TemplateResponse
from django.template import Context
from contacts.filters import ContactFilter, CustomFieldFilter, SegmentFilter


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
    paginate_by = 10

    def get_queryset(self):
        """Filter Custom fields with the user's Company."""
        return AllowedField.objects.filter(belongs_to=self.request.user.company)

    def get_context_data(self, **kwargs):
        """Pass extra data to the template: fields names and filtered queryset."""
        context = super().get_context_data(**kwargs)
        context['fields'] = ['id', 'Field name', 'Field type']
        filterset = CustomFieldFilter(self.request.GET, queryset=self.get_queryset())
        page = self.request.GET.get('page', 1)
        context['paginated_objects'] = self.get_paginator(filterset.qs, self.paginate_by).get_page(page)
        _, page_obj, _, _ = self.paginate_queryset(filterset.qs, self.paginate_by)
        context["page_obj"] = page_obj
        context['create_form'] = CustomFieldForm()
        context['stats_total_fields'] = filterset.qs.count()
        context["existing_obj"] = True if self.get_queryset().only('id').first() else False
        context["filter"] = filterset
        context["active_filters"] = len({k: v for k, v in self.request.GET.items() if k not in ('page', 'order_by', 'name') and v not in ('', None)})
        context["has_any_filters"] = True if {k: v for k, v in self.request.GET.items() if k not in ('order_by', 'page') and v not in ('', None)} else False
        filterset.form.active_filters = context["active_filters"]
        return context



class CreateCustomField(LoginRequiredMixin, FormView, SuccessMessageMixin):
    """View used to create a new custom field."""
    form_class = CustomFieldForm
    success_message = 'Field created successfully.'

    def form_valid(self, form) -> HttpResponse:
        """Override 'form_valid()' to update 'belongs_to' field and return a single line to add to table."""
        field = form.save(commit=False)
        field.belongs_to = self.request.user.company
        field.save()
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(reverse_lazy('contacts:list_custom_fields'))

    def form_invalid(self, form):
        """Override 'form_invalid()' to return the form with errors."""
        messages.error(self.request, 'Error creating field.')
        return HttpResponseRedirect(reverse_lazy('contacts:list_custom_fields'))


class DeleteCustomField(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    """View used to delete a custom field."""
    model = AllowedField
    success_url = reverse_lazy('contacts:list_custom_fields')
    success_message = 'Field deleted successfully.'


class ListSegment(SuccessMessageMixin, LoginRequiredMixin, ListView):
    template_name = 'contacts/list_segments.html'
    paginate_by = 20

    def get_queryset(self):
        """Filter Segments with the user's Company."""
        return Segment.objects.filter(belongs_to=self.request.user.company)

    def get_context_data(self, **kwargs):
        """Pass extra data to the template: fields names and filtered queryset."""
        context = super().get_context_data(**kwargs)
        context['fields'] = ['id', 'Name', 'Description', 'Members']
        context['filter'] = SegmentFilter(self.request.GET, queryset=self.get_queryset())
        return context


class CreateSegment(LoginRequiredMixin, FormView):
    """View used to create a new Segment."""
    template_name = 'contacts/create_segment.html'
    form_class = SegmentForm

    def get_form_kwargs(self):
        """Override 'get_form_kwargs()' to pass the request data to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        """Override 'form_valid()' to update 'belongs_to' field."""
        segment = form.save(commit=False)
        segment.belongs_to = self.request.user.company
        segment.save()
        group_form = GroupForm()
        group = Group.objects.create(belongs_to=self.request.user.company, segment=segment)
        return TemplateResponse(
            self.request,
            'contacts/create_group_conditions.html',
            {'group': group, 'form': group_form, 'segment': segment}
        )


class UpdateGroupSegment(LoginRequiredMixin, FormView):
    """View used to update a Group of filters."""
    form_class = GroupForm

    def form_valid(self, form):
        """Override 'form_valid()' to update 'belongs_to' field."""
        group = Group.objects.get(id=self.kwargs['pk'])
        group.operator = form.cleaned_data['operator']
        group.save()
        print(group.operator, group.id)
        return HttpResponse(status=200)


class AddFilterView(LoginRequiredMixin, CreateView):
    """View used to add a Filter in a Group of filters."""
    def post(self, request, *args, **kwargs):
        """return a new filter form."""
        group = Group.objects.get(id=self.kwargs['pk'])
        filter = Filter.objects.create(belongs_to=self.request.user.company)
        group.filters.add(filter)
        filter.save()
        form = FilterForm(instance=filter)
        return TemplateResponse(
            request=request,
            template='contacts/add_filter_form.html',
            context={'form': form, 'filter': filter}
        )


class UpdateFilterView(LoginRequiredMixin, FormView):
    """View used to update a Filter in a Group of filters."""
    form_class = FilterForm

    def form_valid(self, form):
        """Update Filter fields."""
        filter = Filter.objects.get(id=self.kwargs['pk'])
        for k, v in form.cleaned_data.items():
            setattr(filter, k, v)
        filter.save()
        return HttpResponse(status=200)



class DeleteSegment(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    """View used to delete a Segment."""
    template_name = 'contacts/delete_segment.html'
    model = Segment
    success_url = reverse_lazy('contacts:list_segments')
    success_message = 'Segment deleted successfully.'


class UpdateSegmentView(SuccessMessageMixin, UpdateView, LoginRequiredMixin):
    """View used to update a Segment."""
    template_name = 'contacts/segment_details.html'
    model = Segment
    success_message = "Segment updated successfully."
    success_url = reverse_lazy('contacts:list_segments')
    form_class = SegmentForm

    def get(self, request, *args, **kwargs):
        """Override 'get()' to add the GroupForm() to the context."""
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        groups = Group.objects.filter(segment=self.object).prefetch_related('filters')
        context['group_forms'] = [(GroupForm(instance=group), group.id) for group in groups]
        return TemplateResponse(request, self.template_name, context)

    def get_form_kwargs(self):
        """Override 'get_form_kwargs()' to pass the request data to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        """Override 'form_valid()' to update the user JSONField() accordingly."""
        contact = form.save(commit=False)
        contact.updated_by = self.request.user
        contact.save()
        return super().form_valid(form)
