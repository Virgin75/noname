from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union

from django.conf import settings
from django_rq import get_queue
from rq import Callback, Queue
from rq.defaults import DEFAULT_RESULT_TTL
from rq.utils import backend_class

from commons.models import AsyncTaskLog


class RqJob:  # noqa
    queue_class = Queue

    def __init__(
        self,
        queue: Union["Queue", str],
        connection: Optional["Redis"] = None,
        timeout: Optional[int] = None,
        result_ttl: int = DEFAULT_RESULT_TTL,
        ttl: Optional[int] = None,
        queue_class: Optional[Type["Queue"]] = None,
        depends_on: Optional[List[Any]] = None,
        at_front: bool = False,
        meta: Optional[Dict[Any, Any]] = None,
        description: Optional[str] = None,
        failure_ttl: Optional[int] = None,
        retry: Optional["Retry"] = None,
        on_failure: Optional[Union[Callback, Callable[..., Any]]] = None,
        on_success: Optional[Union[Callback, Callable[..., Any]]] = None,
        on_stopped: Optional[Union[Callback, Callable[..., Any]]] = None,
    ):
        """A decorator that adds a ``delay`` method to the decorated function,
        which in turn creates a RQ job when called. Accepts a required
        ``queue`` argument that can be either a ``Queue`` instance or a string
        denoting the queue name.  For example::

            ..codeblock:python::

                >>> @async_task(queue='default')
                >>> def simple_add(x, y):
                >>>    return x + y
                >>> ...
                >>> # Puts `simple_add` function into queue
                >>> simple_add.delay(1, 2)

        Args:
            queue (Union['Queue', str]): The queue to use, can be the Queue class itself, or the queue name (str)
            connection (Optional[Redis], optional): Redis Connection. Defaults to None.
            timeout (Optional[int], optional): Job timeout. Defaults to None.
            result_ttl (int, optional): Result time to live. Defaults to DEFAULT_RESULT_TTL.
            ttl (Optional[int], optional): Time to live. Defaults to None.
            queue_class (Optional[Queue], optional): A custom class that inherits from `Queue`. Defaults to None.
            depends_on (Optional[List[Any]], optional): A list of dependents jobs. Defaults to None.
            at_front (Optional[bool], optional): Whether to enqueue the job at front of the queue. Defaults to None.
            meta (Optional[Dict[Any, Any]], optional): Arbitraty metadata about the job. Defaults to None.
            description (Optional[str], optional): Job description. Defaults to None.
            failure_ttl (Optional[int], optional): Failture time to live. Defaults to None.
            retry (Optional[Retry], optional): A Retry object. Defaults to None.
            on_failure (Optional[Union[Callback, Callable[..., Any]]], optional): Callable to run on failure. Defaults
                to None.
            on_success (Optional[Union[Callback, Callable[..., Any]]], optional): Callable to run on success. Defaults
                to None.
            on_stopped (Optional[Union[Callback, Callable[..., Any]]], optional): Callable to run when stopped. Defaults
                to None.
        """
        self.queue = queue
        self.queue_class = backend_class(self, "queue_class", override=queue_class)
        self.connection = connection
        self.timeout = timeout
        self.result_ttl = result_ttl
        self.ttl = ttl
        self.meta = meta
        self.depends_on = depends_on
        self.at_front = at_front
        self.description = description
        self.failure_ttl = failure_ttl
        self.retry = retry
        self.on_success = on_success
        self.on_failure = on_failure
        self.on_stopped = on_stopped

    def __call__(self, f):
        @wraps(f)
        def delay(*args, **kwargs):
            if isinstance(self.queue, str):
                queue = self.queue_class(name=self.queue, connection=self.connection)
            else:
                queue = self.queue

            depends_on = kwargs.pop("depends_on", None)
            job_id = kwargs.pop("job_id", None)
            at_front = kwargs.pop("at_front", False)

            if not depends_on:
                depends_on = self.depends_on

            if not at_front:
                at_front = self.at_front

            belongs_to = kwargs.pop("belongs_to")
            log = AsyncTaskLog.objects.create(
                task_name=f.__name__,
                is_periodic=False,
                status="running",
                args=args,
                kwargs=kwargs,
                belongs_to_id=belongs_to,
            )
            kwargs["task_log_id"] = log.id
            kwargs["belongs_to_id"] = belongs_to
            return queue.enqueue_call(
                f,
                args=args,
                kwargs=kwargs,
                timeout=self.timeout,
                result_ttl=self.result_ttl,
                ttl=self.ttl,
                depends_on=depends_on,
                job_id=job_id,
                at_front=at_front,
                meta=self.meta,
                description=self.description,
                failure_ttl=self.failure_ttl,
                retry=self.retry,
                on_failure=self.on_failure,
                on_success=self.on_success,
                on_stopped=self.on_stopped,
            )

        f.delay = delay
        return f


def async_task(func_or_queue, connection=None, *args, **kwargs):
    """
    The same as RQ's job decorator, but it automatically works out
    the ``connection`` argument from RQ_QUEUES.

    And also, it allows simplified ``@job`` syntax to put job into
    default queue.

    If RQ.DEFAULT_RESULT_TTL setting is set, it is used as default
    for ``result_ttl`` kwarg.
    """
    if callable(func_or_queue):
        func = func_or_queue
        queue = "default"
    else:
        func = None
        queue = func_or_queue

    if isinstance(queue, str):
        try:
            queue = get_queue(queue)
            if connection is None:
                connection = queue.connection
        except KeyError:
            pass

    RQ = getattr(settings, "RQ", {})
    default_result_ttl = RQ.get("DEFAULT_RESULT_TTL")
    if default_result_ttl is not None:
        kwargs.setdefault("result_ttl", default_result_ttl)

    decorator = RqJob(queue, connection=connection, *args, **kwargs)
    if func:
        return decorator(func)
    return decorator
