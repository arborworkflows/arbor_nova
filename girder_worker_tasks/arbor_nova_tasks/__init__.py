from girder_worker import GirderWorkerPluginABC


class ArborNovaTasksGirderWorkerPlugin(GirderWorkerPluginABC):
    def __init__(self, app, *args, **kwargs):
        self.app = app

    def task_imports(self):
        # Return a list of python importable paths to the
        # plugin's path directory
        return [
            'arbor_nova_tasks.arbor_tasks.app_support',
            'arbor_nova_tasks.arbor_tasks.core',
            'arbor_nova_tasks.arbor_tasks.fnlcr',
            'arbor_nova_tasks.arbor_tasks.example'
        ]
