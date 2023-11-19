from django.db import models


class HistoryMixin(models.Model):
    """Store the history of the model. This is an abstract class, other models need to inherit it."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey("users.Account", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True
