#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.plugin import getPlugin, GirderPlugin
from girder.models.user import User
from .client_webroot import ClientWebroot
from . import rest


class ArborNovaGirderPlugin(GirderPlugin):
    DISPLAY_NAME = 'Arbor Nova'

    def _create_anonymous_user(self):
        ANONYMOUS_USER = 'anonymous'
        ANONYMOUS_PASSWORD = 'letmein'

        anon_user = User().findOne({
            'login': ANONYMOUS_USER
        })

        if not anon_user:
            anon_user = User().createUser(
                login=ANONYMOUS_USER,
                password=ANONYMOUS_PASSWORD,
                firstName='Public',
                lastName='User',
                email='anon@example.com',
                admin=False,
                public=False)
            anon_user['status'] = 'enabled'

            anon_user = User().save(anon_user)
        return anon_user

    def load(self, info):
        # Relocate Girder
        info['serverRoot'], info['serverRoot'].girder = (ClientWebroot(),
                                                         info['serverRoot'])
        info['serverRoot'].api = info['serverRoot'].girder.api
        self._create_anonymous_user()
        getPlugin('jobs').load(info)
        info['apiRoot'].arbor_nova = rest.ArborNova()
