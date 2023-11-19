from django.contrib import admin

from users.models import Account, Company

# Register your models here.

admin.site.register(Account)
admin.site.register(Company)
