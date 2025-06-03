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
            logger.info("Loading Data from the source")
            created, updated, loaded = load_data(path)
            logger.info("Succesfully loaded the requested types", created)
        except Exception as e:
            logger.info("Failed to load the requested types ", e)
