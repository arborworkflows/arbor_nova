#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.plugin import getPlugin, GirderPlugin
from girder.models.user import User
from . import rest


class ArborNovaGirderPlugin(GirderPlugin):
    DISPLAY_NAME = 'Arbor Nova'

    def load(self, info):
        ANONYMOUS_USER = 'anonymous'

        anon_user = User().findOne({
            'login': ANONYMOUS_USER
        })

        if not anon_user:
            anon_user = User().createUser(
                login=ANONYMOUS_USER,
                password=None,
                firstName='Public',
                lastName='User',
                email='anon@example.com',
                admin=False,
                public=False)
            anon_user['status'] = 'enabled'

            anon_user = User().save(anon_user)

        getPlugin('jobs').load(info)
        info['apiRoot'].arbor_nova = rest.ArborNova(ANONYMOUS_USER)
