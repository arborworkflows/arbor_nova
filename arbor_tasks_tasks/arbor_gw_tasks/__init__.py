import os
import shutil
import tempfile
from girder_worker import GirderWorkerPluginABC
from girder_worker.app import app
from girder_worker.utils import girder_job
from girder_worker_utils.transforms import girder_io


class ArborTasksPlugin(GirderWorkerPluginABC):
    def __init__(self, app, *args, **kwargs):
        self.app = app

    def task_imports(self):
        # Return a list of python importable paths to the
        # plugin's path directory
        return ['arbor_gw_tasks.hello']


@girder_job(title='ColumnAppendTask')
@app.task(bind=True)
def column_append(self, in_filepath, output_item_id, **kwargs):
    tmpdir = tempfile.mkdtemp()
    outname = 'outfile.csv'

    # Ensure the file is read/write by the creator only
    saved_umask = os.umask(0o077)

    outpath = os.path.join(tmpdir, outname)
    try:
        with open(outpath, 'w') as tmp:
            with open(in_filepath, 'r') as csv:
                for line in csv:
                    outline = line.strip() + ', newcol\n'
                    tmp.write(outline)
        guti = girder_io.GirderUploadToItem(output_item_id, gc=self.girder_client)
        guti.transform(tmp.name)
    finally:
        os.umask(saved_umask)
        shutil.rmtree(tmpdir, ignore_errors=True)

    return 'celery got string %s' % in_filepath
