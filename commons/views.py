from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(TemplateView, LoginRequiredMixin):
    template_name = 'commons/home.html'


class OrderingMixin:
    ordering_fields = []
    ordering_type = "desc"  # asc or desc

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', "id")
        ordering = ordering if self.ordering_type == "asc" else f"-{ordering}"
        return ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context | {'ordering_fields': self.ordering_fields}
