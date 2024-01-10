from django.urls import path

from commons.views import DownloadExport, HomeView, ListExport

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("exports/", ListExport.as_view(), name="list_exports"),
    path("exports/<int:pk>/", DownloadExport.as_view(), name="download_export"),
]
