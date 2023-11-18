from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(TemplateView, LoginRequiredMixin):
    template_name = 'commons/home.html'


class FilterMixin:
    filterset_class = None

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        extra_context = {}
        filterset = self.filterset_class(self.request.GET, queryset=self.get_queryset(), request=self.request)
        page = self.request.GET.get('page', 1)
        extra_context['paginated_objects'] = self.get_paginator(filterset.qs, self.paginate_by).get_page(page)
        _, page_obj, _, _ = self.paginate_queryset(filterset.qs, self.paginate_by)
        extra_context["page_obj"] = page_obj
        context["existing_obj"] = True if self.get_queryset().first() else False
        context["filter"] = filterset
        context["active_filters"] = len({k: v for k, v in self.request.GET.items() if
                                         k not in ('page', 'order_by', 'name') and v not in ('', None)})
        context["has_any_filters"] = True if {k: v for k, v in self.request.GET.items() if
                                              k not in ('order_by', 'page') and v not in ('', None)} else False
        filterset.form.active_filters = context["active_filters"]
        return context | extra_context
