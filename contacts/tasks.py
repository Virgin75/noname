import logging
import traceback

import pandas as pd
from django.apps import apps
from django.conf import settings
from django.utils import timezone

from commons.decorators import async_task
from commons.models import AsyncTaskLog, ExportLog

logger = logging.getLogger("rq.worker")


@async_task("high")
def generate_export_task(model: str, app: str, task_log_id: int = None, **kwargs):
    """
    Async task called to generate an export file.

    Parameters
    ----------
    model : str
        The name of the Django model on which we are exporting objects. e.g. 'contact'
    app : str
        The name of the Django app where the 'model' is located. e.g. 'contacts'
    task_log_id : int, Optional
        The ID of the 'AsyncTaskLog' object created when the task was scheduled.
        This kwargs is automatically passed when 'task.delay()' is called.
    kwargs : dict
        Extra filters to apply on the queryset. Can be used to filter the objects to export.
    """
    log = AsyncTaskLog.objects.get(id=task_log_id)
    log.status = "running"
    log.save()
    try:
        logger.info(f" 🏁 Starting 'generate_export_task' for task: '{log.id}'...")
        extra_filters = {k: v for k, v in kwargs.items() if k not in ("task_log_id")}
        ModelClass = apps.get_model(model_name=model, app_label=app)  # noqa
        queryset = ModelClass.objects.export(**extra_filters)

        # Convert queryset to pandas dataframe and save to csv
        df = pd.DataFrame(queryset)
        file_path = settings.EXPORT_ROOT + "/" + f"{app}_{model}_{timezone.now().strftime('%Y-%m-%d')}.csv"
        df.to_csv(file_path, index=False)
        ExportLog.objects.create(
            file_name=file_path.split("/")[-1],
            file_path=file_path,
            total_rows=df.shape[0],
            total_columns=df.shape[1],
            type=model,
            belongs_to=log.belongs_to,
        )

        log.ended_at = timezone.now()
        log.status = "completed"
        log.save()
        logger.info(f" ✅️ Successfully completed 'generate_export_task' for task: '{log.id}'")
    except:
        logger.exception(f" ❌ Error while generating export for task: '{task_log_id}'")
        log.status = "failed"
        log.error_traceback = traceback.format_exc()
        log.ended_at = timezone.now()
        log.save()
