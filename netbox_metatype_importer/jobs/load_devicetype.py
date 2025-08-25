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
            loaded, created, updated = load_data(path)
            logger.info(f"Successfully loaded types: loaded={loaded}, created={created}, updated={updated}")
        except Exception as e:
            logger.exception("Failed to load the requested types: %s", e)
