from netbox.jobs import JobRunner
import logging

from ..utils import load_data

logger = logging.getLogger(__name__)


class LoadData(JobRunner):
    class Meta:
        name = "LoadData"

    def run(self, *args, **kwargs):
        path = kwargs.get("path")
        try:
            self.logger.info(f"Loading data from GitHub: {path}")
            loaded, created, updated = load_data(
                path,
                job_logger=self.logger,
                job=self.job,
            )
            self.logger.info(f"Loading completed: loaded={loaded}, " f"created={created}, updated={updated}")
        except Exception as e:
            self.logger.exception(f"Failed to load device types from GitHub: {path}")
            raise
