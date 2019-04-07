import pytest

from girder.plugin import loadedPlugins


@pytest.mark.plugin('arbor_tasks')
def test_import(server):
    assert 'arbor_tasks' in loadedPlugins()
