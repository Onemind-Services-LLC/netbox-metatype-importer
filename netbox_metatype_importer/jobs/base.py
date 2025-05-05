import logging
import time
import traceback
from contextlib import ExitStack

from core.choices import JobStatusChoices
from core.models import Job
from core.signals import clear_events
from django.db import transaction
from django.utils import timezone
from extras.choices import LogLevelChoices
from netbox.jobs import JobRunner as BaseJobRunner
from netbox.registry import registry
from utilities.exceptions import AbortScript, AbortTransaction
from utilities.serialization import serialize_object

__all__ = ["JobRunner"]

logger = logging.getLogger("netbox.plugins.netbox_saltstack")


class JobRunner(BaseJobRunner):
    """
    A custom JobRunner for NetBox jobs that:
      1) Wraps job execution within a database transaction (atomic).
      2) Catches exceptions like AbortTransaction or AbortScript.
      3) Logs messages to both an in-memory list (self.messages) and standard Python logs.
      4) Collects 'output' from the job for final reporting.

    Subclasses must implement the `run_job()` method for their specific logic.
    """

    def __init__(self, job):
        """
        Initialize the runner for a specific NetBox job.
        """
        super().__init__(job)
        self.output = ""
        self.messages = []
        self.failed = False

    def _log(self, message: str, obj=None, level=logging.INFO):
        """
        Internal helper to unify the logging process:
         - Map Python log levels to NetBox job log levels.
         - Append to self.messages (for the job's own data storage).
         - Log to the standard Python logger.
        """
        level_map = {
            logging.DEBUG: LogLevelChoices.LOG_DEBUG,
            logging.INFO: LogLevelChoices.LOG_INFO,
            logging.WARNING: LogLevelChoices.LOG_WARNING,
            logging.ERROR: LogLevelChoices.LOG_FAILURE,
            logging.CRITICAL: LogLevelChoices.LOG_FAILURE,
        }
        nb_level = level_map.get(level, LogLevelChoices.LOG_INFO)

        # Append to the in-memory list of messages
        self.messages.append(
            {
                "time": timezone.now().isoformat(),
                "status": nb_level,
                "message": str(message),
                "obj": str(obj) if obj else None,
            }
        )

        # Also record to the system (Python) log
        logger.log(level, message)

    #
    # Public log methods for convenience
    #
    def log_debug(self, message, obj=None):
        self._log(message, obj, logging.DEBUG)

    def log_info(self, message, obj=None):
        self._log(message, obj, logging.INFO)

    def log_warning(self, message, obj=None):
        self._log(message, obj, logging.WARNING)

    def log_failure(self, message, obj=None):
        self._log(message, obj, logging.ERROR)
        self.failed = True

    #
    # Execution
    #
    def run(self, *args, **kwargs):
        """
        Overriding BaseJobRunner.run(). This is automatically called by NetBox's
        job scheduler. We wrap the job logic in a transaction and handle
        exceptions uniformly.
        """
        self.log_info(f"Running job '{self.job.name}' (ID: {self.job.id})")
        request = kwargs.get("request", None)

        try:
            try:
                # Execute the job. Wrap it with the event_tracking context manager to ensure we process
                # change logging, event rules, etc.
                with ExitStack() as stack:
                    for request_processor in registry["request_processors"]:
                        stack.enter_context(request_processor(request))

                    with transaction.atomic():
                        # Capture and store any 'output' returned by run_job()
                        self.output = self.run_job(*args, **kwargs)

            except AbortTransaction:
                self.log_info("Database changes have been reverted automatically.")
                if self.failed:
                    self.log_warning("Job failed")

        except Exception as e:
            # Handle both AbortScript and any other exceptions
            if isinstance(e, AbortScript):
                self.log_failure(f"Job '{self.job.name}' aborted with error: {e}")
            else:
                # Provide a stack trace for unhandled exceptions
                stacktrace = traceback.format_exc()
                self.log_failure(f"An exception occurred: `{type(e).__name__}: {stacktrace}`")

            # If it wasn't just a deliberate transaction rollback, note that changes are reverted
            if not isinstance(e, AbortTransaction):
                self.log_info("Database changes have been reverted due to error.")

            if request:
                clear_events.send(request)
            raise

        finally:
            # Always update the job's data with logs, output, etc.
            self.job.data = self.get_job_data()

    def run_job(self, wait_for_job=None, *args, **kwargs):
        """
        Execute the main job logic, optionally waiting on another job to finish first.

        If the `wait_for_job` argument is provided, this method will poll the status
        of that job every five seconds until it has either completed or errored.
        If `wait_for_job` is not a valid `Job` instance, an `AbortScript` exception
        is raised immediately.

        Subclasses that override `run_job()` must invoke `super().run_job(...)` to
        retain this waiting logic. After calling `super().run_job(...)`, they can
        implement any additional logic required for the job.
        """
        if wait_for_job:
            if not isinstance(wait_for_job, Job):
                raise AbortScript(f"Expected {wait_for_job} to be a Job instance, received {type(wait_for_job)}")

            while wait_for_job.status is not [
                JobStatusChoices.STATUS_COMPLETED,
                JobStatusChoices.STATUS_ERRORED,
            ]:
                self.log_info(f"Waiting for job {wait_for_job.name} to complete")
                wait_for_job.refresh_from_db()
                time.sleep(5)

    def get_job_data(self) -> dict:
        """
        Return any data to be stored on the NetBox Job record after completion.
        By default, this includes the in-memory messages and any 'output' text.
        """
        return {
            "messages": self.messages,
            "output": self.output,
        }

    def serialize_object(self, instance) -> dict:
        """
        Helper to serialize a NetBox object (or other object) for logging
        or storing in messages. If the object has a custom 'serialize_object()',
        use it; otherwise fall back to NetBox's built-in 'serialize_object()'.
        """
        if hasattr(instance, "serialize_object"):
            obj = instance.serialize_object()
        else:
            obj = serialize_object(instance)

        return {
            "id": instance.id,
            "_type": f"{instance._meta.app_label}.{instance._meta.model_name}",
            **obj,
        }
