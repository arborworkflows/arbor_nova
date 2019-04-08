#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.plugin import getPlugin, GirderPlugin
from . import rest


class ArborNovaGirderPlugin(GirderPlugin):
    DISPLAY_NAME = 'Arbor Nova'

    def load(self, info):
        getPlugin('jobs').load(info)

        info['apiRoot'].arbor_nova = rest.ArborNova()
