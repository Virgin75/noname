from django.urls import path
from contacts.views import ListContact, CreateContact, ListCustomField, CreateCustomField, DeleteCustomField, DeleteContact, UpdateContactView

urlpatterns = [
    path('contacts', ListContact.as_view(), name='list_contacts'),
    path('contacts/add', CreateContact.as_view(), name='create_contact'),
    path('contacts/<int:pk>/delete', DeleteContact.as_view(), name='delete_contact'),
    path('contacts/<int:pk>/update', UpdateContactView.as_view(), name='update_contact'),
    path('fields', ListCustomField.as_view(), name='list_custom_fields'),
    path('fields/add', CreateCustomField.as_view(), name='create_custom_field'),
    path('fields/<int:pk>/delete', DeleteCustomField.as_view(), name='delete_custom_field'),
]
