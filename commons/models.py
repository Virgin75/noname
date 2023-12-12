from django.db import models


class HistoryMixin(models.Model):
    """Store the history of the model. This is an abstract class, other models need to inherit it."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    updated_by = models.ForeignKey("users.Account", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True


class ExportLog(models.Model):
    """Store the export files generated. ExportLogs are deleted automatically 72h after creation."""

    STATUS = (
        ("running", "Running"),
        ("failed", "Failed"),
        ("completed", "Completed"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=100)
    file_path = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS, default=STATUS[0][0])
    belongs_to = models.ForeignKey("users.Company", on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=25, null=True, blank=True)
    total_rows = models.IntegerField(null=True, blank=True)
    total_columns = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey("users.Account", on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def final_size(self) -> str:
        """Return the size of the file in a human-readable format."""
        if self.total_rows and self.total_columns:
            return f"{self.total_rows} lines x {self.total_columns} columns"
        return ""


class AsyncTaskLog(models.Model):
    """Logs all the async Task executed."""

    STATUS = (
        ("pending", "Pending"),
        ("running", "Running"),
        ("failed", "Failed"),
        ("completed", "Completed"),
    )
    task_name = models.CharField(max_length=100)
    is_periodic = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default=STATUS[0][0])
    error_traceback = models.TextField(null=True, blank=True)
    args = models.JSONField(default=list)
    kwargs = models.JSONField(default=dict)
    belongs_to = models.ForeignKey("users.Company", on_delete=models.CASCADE, null=True, blank=True)

    @property
    def duration(self) -> float | None:
        """Return the total duration of the task in seconds."""
        if self.created_at and self.ended_at:
            return (self.ended_at - self.created_at).total_seconds()
        return None
