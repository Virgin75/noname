from django.urls import path

from commons.views import HomeView, ListExport

urlpatterns = [
    path("home/", HomeView.as_view(), name="home"),
    path("exports/", ListExport.as_view(), name="list_exports"),
]
