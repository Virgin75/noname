import datetime
import pickle

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.fields.json import KT
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, Template
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import (
    BaseUpdateView,
    CreateView,
    DeleteView,
    FormView,
    UpdateView,
)
from django.views.generic.list import ListView

from commons.views import FilterMixin, OrPermissionsMixin
from contacts.filters import (
    ContactFilter,
    CustomFieldFilter,
    ExportContactFilters,
    SegmentFilter,
)
from contacts.forms import (
    ContactForm,
    CustomFieldForm,
    FilterForm,
    GroupForm,
    SegmentForm,
)
from contacts.models import AllowedField, Contact, Filter, Group, Segment


class CreateContact(SuccessMessageMixin, LoginRequiredMixin, FormView):
    """View used to create a new Contact with its custom fields values."""

    form_class = ContactForm
    success_message = "Contact created successfully."

    def form_valid(self, form):
        """Update the user JSONField() accordingly."""
        contact = form.save(commit=False)
        contact.belongs_to = self.request.user.company
        contact.updated_by = self.request.user
        custom_fields = {}
        for k, v in form.cleaned_data.items():
            if k.startswith("fields__"):
                if isinstance(v, datetime.date):
                    v = v.strftime("%Y-%m-%d")
                custom_fields[k[8:]] = v
        contact.fields = custom_fields
        contact.save()
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(reverse_lazy("contacts:list_contacts"))

    def form_invalid(self, form):
        """Return the form with errors."""
        messages.error(self.request, "Error creating Contact.")
        return HttpResponseRedirect(reverse_lazy("contacts:list_contacts"))

    def get_form_kwargs(self):
        """Override 'get_form_kwargs()' to pass the request data to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class ListContact(SuccessMessageMixin, FilterMixin, LoginRequiredMixin, ListView):
    template_name = "contacts/list_contacts.html"
    filterset_class = ContactFilter
    paginate_by = 10

    def get_queryset(self):
        fields = AllowedField.objects.filter(belongs_to=self.request.user.company).values_list("name", flat=True)
        annotations = {field: KT(f"fields__{field}") for field in fields}
        return (
            Contact.objects.filter(belongs_to=self.request.user.company)
            .values("id", "email", "created_at", "updated_at", "updated_by")
            .annotate(**annotations)
            .values("id", "email", *fields, "created_at", "updated_at", "updated_by")
        )

    def get_context_data(self, **kwargs):
        """Pass extra data to the template: fields names and filtered queryset."""
        context = super().get_context_data(**kwargs)
        context["fields"] = (
            {"": "sticky", "Email": "sticky"}
            | {
                f: None
                for f in list(
                    AllowedField.objects.filter(belongs_to=self.request.user.company).values_list("name", flat=True)
                )
            }
            | {"Creation date": None, "Last update date": None, "Updated by": None}
        )
        context["create_form"] = ContactForm(request=self.request)
        context["export_filters"] = ExportContactFilters()
        context["stats_total_contacts"] = context["filter"].qs.count()
        last_30_days = datetime.datetime.now() - datetime.timedelta(days=30)
        last_7_days = datetime.datetime.now() - datetime.timedelta(days=7)
        today_min = datetime.datetime.combine(timezone.now().date(), datetime.datetime.today().time().min)
        today_max = datetime.datetime.combine(timezone.now().date(), datetime.datetime.today().time().max)
        context["stats_contacts_last_30d"] = (
            context["filter"].qs.filter(created_at__gte=last_30_days).values("id").count()
        )
        context["stats_contacts_last_7d"] = (
            context["filter"].qs.filter(created_at__gte=last_7_days).values("id").count()
        )
        context["stats_contacts_today"] = (
            context["filter"].qs.filter(created_at__range=(today_min, today_max)).values("id").count()
        )
        context["stats_contacts_status"] = context["filter"].qs.aggregate(
            count_sub=Count("id", filter=Q(is_unsubscribed=None) | Q(is_unsubscribed=False)),
            count_unsub=Count("is_unsubscribed", filter=Q(is_unsubscribed=True)),
        )
        return context


class UpdateContactView(SuccessMessageMixin, UpdateView, LoginRequiredMixin):
    """View used to update a Contact."""

    template_name = "contacts/contact_details.html"
    model = Contact
    success_message = "Contact updated successfully."
    success_url = reverse_lazy("contacts:list_contacts")
    form_class = ContactForm

    def get_form_kwargs(self):
        """Override 'get_form_kwargs()' to pass the request data to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["custom_fields_values"] = self.object.fields
        return kwargs

    def form_valid(self, form):
        """Override 'form_valid()' to update the user JSONField() accordingly."""
        contact = form.save(commit=False)
        contact.updated_by = self.request.user
        custom_fields = {}
        for k, v in form.cleaned_data.items():
            if k.startswith("fields__"):
                if isinstance(v, datetime.date):
                    v = v.strftime("%Y-%m-%d")
                custom_fields[k[8:]] = v
        contact.fields = custom_fields
        contact.save()
        return super().form_valid(form)


class DeleteContact(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    """View used to delete a Contact."""

    model = Contact
    success_url = reverse_lazy("contacts:list_contacts")
    success_message = "Contact deleted successfully."


class ExportContacts(SuccessMessageMixin, LoginRequiredMixin, FormView):
    """View used to export Contacts."""

    form_class = ExportContactFilters
    success_message = "Export file is being generated..."
    success_url = reverse_lazy("commons:list_exports")

    def form_valid(self, form):
        """Override 'form_valid()' to update the user JSONField() accordingly."""
        from contacts.tasks import generate_export_task

        cleaned_dates = {
            k: v.strftime("%Y-%m-%d") for k, v in form.cleaned_data.items() if isinstance(v, datetime.date)
        }
        generate_export_task.delay(
            "contact",
            "contacts",
            user_id=self.request.user.id,
            belongs_to=self.request.user.company.id,
            **cleaned_dates,
        )
        return super().form_valid(form)


class ListCustomField(OrPermissionsMixin, SuccessMessageMixin, FilterMixin, LoginRequiredMixin, ListView):
    template_name = "contacts/list_custom_fields.html"
    filterset_class = CustomFieldFilter
    paginate_by = 10
    permission_required = ("users.contacts_full_access", "users.contacts_read_only_access")

    def get_queryset(self):
        """Filter Custom fields with the user's Company."""
        return AllowedField.objects.filter(belongs_to=self.request.user.company)

    def get_context_data(self, **kwargs):
        """Pass extra data to the template: fields names and filtered queryset."""
        context = super().get_context_data(**kwargs)
        context["fields"] = ["", "Field name", "Field type"]
        context["create_form"] = CustomFieldForm()
        context["stats_total_fields"] = context["filter"].qs.count()
        return context


class CreateCustomField(PermissionRequiredMixin, LoginRequiredMixin, FormView, SuccessMessageMixin):
    """View used to create a new custom field."""

    form_class = CustomFieldForm
    success_message = "Field created successfully."
    permission_required = "users.contacts_full_access"

    def form_valid(self, form) -> HttpResponse:
        """Override 'form_valid()' to update 'belongs_to' field and return a single line to add to table."""
        field = form.save(commit=False)
        field.belongs_to = self.request.user.company
        field.save()
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(reverse_lazy("contacts:list_custom_fields"))

    def form_invalid(self, form):
        """Override 'form_invalid()' to return the form with errors."""
        messages.error(self.request, "Error creating field.")
        return HttpResponseRedirect(reverse_lazy("contacts:list_custom_fields"))


class DeleteCustomField(PermissionRequiredMixin, SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    """View used to delete a custom field."""

    model = AllowedField
    success_url = reverse_lazy("contacts:list_custom_fields")
    success_message = "Field deleted successfully."
    permission_required = "users.contacts_full_access"


class ListSegment(SuccessMessageMixin, LoginRequiredMixin, FilterMixin, ListView):
    """View used to list existing Segments for the current user."""

    template_name = "contacts/list_segments.html"
    filterset_class = SegmentFilter
    paginate_by = 10

    def get_queryset(self):
        """Filter Segments with the user's Company."""
        return Segment.objects.filter(belongs_to=self.request.user.company)

    def get_context_data(self, **kwargs):
        """Pass extra data to the template: fields names and filtered queryset."""
        context = super().get_context_data(**kwargs)
        context["fields"] = ["", "Segment name", "Description", "Subscribers in segment", ""]
        context["create_form"] = SegmentForm()
        context["stats_total_segments"] = context["filter"].qs.count()
        return context


class CreateSegment(SuccessMessageMixin, LoginRequiredMixin, FormView):
    """View used to create a new Segment."""

    template_name = "contacts/create_segment.html"
    form_class = SegmentForm
    success_message = "Segment created successfully."

    def form_invalid(self, form):
        """Override 'form_invalid()' to return the form with errors."""
        messages.error(self.request, "Error creating field.")
        return HttpResponseRedirect(reverse_lazy("contacts:list_custom_fields"))

    def form_valid(self, form):
        """Override 'form_valid()' to update 'belongs_to' field."""
        segment = form.save(commit=False)
        segment.belongs_to = self.request.user.company
        segment.save()
        return HttpResponseRedirect(reverse_lazy("contacts:segment_details", kwargs={"pk": segment.id}))


class UpdateGroupSegment(LoginRequiredMixin, FormView):
    """View used to update a Group of filters."""

    form_class = GroupForm

    def form_valid(self, form):
        """Override 'form_valid()' to update 'belongs_to' field."""
        group = Group.objects.get(id=self.kwargs["pk"])
        group.operator = form.cleaned_data["operator"]
        group.save()
        print(group.operator, group.id)
        return HttpResponse(status=200)


class AddFilterView(LoginRequiredMixin, CreateView):
    """View used to add a Filter in a Group of filters."""

    def post(self, request, *args, **kwargs):
        """return a new filter form."""
        group = Group.objects.get(id=self.kwargs["pk"])
        filter = Filter.objects.create(belongs_to=self.request.user.company)
        group.filters.add(filter)
        filter.save()
        form = FilterForm(instance=filter)
        return TemplateResponse(
            request=request, template="contacts/add_filter_form.html", context={"form": form, "filter": filter}
        )


class UpdateFilterView(LoginRequiredMixin, FormView):
    """View used to update a Filter in a Group of filters."""

    form_class = FilterForm

    def form_valid(self, form):
        """Update Filter fields."""
        filter = Filter.objects.get(id=self.kwargs["pk"])
        for k, v in form.cleaned_data.items():
            setattr(filter, k, v)
        filter.save()
        return HttpResponse(status=200)


class DeleteSegment(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    """View used to delete a Segment."""

    model = Segment
    success_url = reverse_lazy("contacts:list_segments")
    success_message = "Segment deleted successfully."


class UpdateSegmentView(SuccessMessageMixin, UpdateView, LoginRequiredMixin):
    """View used to update a Segment."""

    template_name = "contacts/segment_details.html"
    model = Segment
    success_message = "Segment updated successfully."
    success_url = reverse_lazy("contacts:list_segments")
    form_class = SegmentForm

    def get(self, request, *args, **kwargs):
        """Override 'get()' to add the GroupForm() to the context."""
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        groups = Group.objects.filter(segment=self.object).prefetch_related("filters")
        context["group_forms"] = [(GroupForm(instance=group), group.id) for group in groups]
        return TemplateResponse(request, self.template_name, context)

    def get_form_kwargs(self):
        """Pass the request data to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        """Update the user's `JSONField()` accordingly."""
        contact = form.save(commit=False)
        contact.updated_by = self.request.user
        contact.save()
        return super().form_valid(form)
