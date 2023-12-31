from django.urls import path

from contacts.views import (
    AddFilterView,
    CreateContact,
    CreateCustomField,
    CreateSegment,
    DeleteContact,
    DeleteCustomField,
    DeleteSegment,
    ExportContacts,
    ListContact,
    ListCustomField,
    ListSegment,
    UpdateContactView,
    UpdateFilterView,
    UpdateGroupSegment,
    UpdateSegmentView,
)

urlpatterns = [
    path("contacts", ListContact.as_view(), name="list_contacts"),
    path("contacts/add", CreateContact.as_view(), name="create_contact"),
    path("contacts/<int:pk>/delete", DeleteContact.as_view(), name="delete_contact"),
    path("contacts/<int:pk>", UpdateContactView.as_view(), name="update_contact"),
    path("contacts/export", ExportContacts.as_view(), name="export_contacts"),
    path("fields", ListCustomField.as_view(), name="list_custom_fields"),
    path("fields/add", CreateCustomField.as_view(), name="create_custom_field"),
    path("fields/<int:pk>/delete", DeleteCustomField.as_view(), name="delete_custom_field"),
    path("segments", ListSegment.as_view(), name="list_segments"),
    path("segments/add", CreateSegment.as_view(), name="create_segment"),
    path("segments/<int:pk>/delete", DeleteSegment.as_view(), name="delete_segment"),
    path("segments/<int:pk>", UpdateSegmentView.as_view(), name="segment_details"),
    path("groups/<int:pk>/update", UpdateGroupSegment.as_view(), name="update_group_segment"),
    path("groups/<int:pk>/add_filter", AddFilterView.as_view(), name="add_filter"),
    path("filters/<int:pk>/update", UpdateFilterView.as_view(), name="update_filter"),
]
