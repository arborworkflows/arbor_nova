from girder_worker import GirderWorkerPluginABC
from girder_worker.app import app
from girder_worker.utils import girder_job


class ArborNovaTasksGirderWorkerPlugin(GirderWorkerPluginABC):
    def __init__(self, app, *args, **kwargs):
        self.app = app

    def task_imports(self):
        # Return a list of python importable paths to the
        # plugin's path directory
        return ['arbor_nova_tasks.column_append']


@girder_job(title='ColumnAppendTask')
@app.task(bind=True)
def column_append(self, in_filepath, **kwargs):
    outname = 'outfile.csv'
    with open(outname, 'w') as tmp:
        with open(in_filepath, 'r') as csv:
            for line in csv:
                outline = line.strip() + ', newcol\n'
                tmp.write(outline)

    return outname
