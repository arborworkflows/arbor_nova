#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.plugin import getPlugin, GirderPlugin
from . import rest


class ArborTasksPlugin(GirderPlugin):
    DISPLAY_NAME = 'arbor_tasks'

    def load(self, info):
        getPlugin('jobs').load(info)

        info['apiRoot'].arbor_task = rest.ArborTask()
