import datetime

from django.db import models
from django.db.models.fields.json import KT


class ContactExportManager(models.Manager):
    def export(
        self, date_start: datetime.date = None, date_end: datetime.date = None, belongs_to_id: int = None
    ):  # noqa
        """
        Define a custom method to export contacts.

        Usage : 'Contact.objects.export(date_start, date_end, belongs_to_id)'
        """
        from contacts.models import AllowedField

        fields = AllowedField.objects.filter(belongs_to_id=belongs_to_id).values_list("name", flat=True)
        annotations = {field: KT(f"fields__{field}") for field in fields}
        extra_filters = {}
        if date_start:
            extra_filters["created_at__gte"] = date_start
        if date_end:
            extra_filters["created_at__lte"] = date_end

        qs = (
            self.filter(belongs_to_id=belongs_to_id, **extra_filters)
            .values("id", "email", "created_at", "updated_at", "updated_by", "is_unsubscribed", "unsubscribed_date")
            .annotate(**annotations)
            .values(
                "id", "email", *fields, "created_at", "updated_at", "updated_by", "is_unsubscribed", "unsubscribed_date"
            )
        )
        return qs.iterator(chunk_size=500)
