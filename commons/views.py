from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(TemplateView, LoginRequiredMixin):
    template_name = 'commons/home.html'

