from netbox_metatype_importer.jobs.base import JobRunner
from ..utils import load_data


class LoadData(JobRunner):
    class Meta:
        name = "LoadData"

    def run_job(self, wait_for_job=None, *args, **kwargs):
        super().run_job(wait_for_job=wait_for_job, *args, **kwargs)
        path = kwargs.get("path")
        created, updated, loaded = load_data(path)
        print("Output is coming : .....", created, updated, loaded)
