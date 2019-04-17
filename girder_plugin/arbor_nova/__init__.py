#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.plugin import getPlugin, GirderPlugin
from girder.models.user import User
from girder.models.collection import Collection
from girder.models.folder import Folder
from . import rest


class ArborNovaGirderPlugin(GirderPlugin):
    DISPLAY_NAME = 'Arbor Nova'

    def _create_result_folder(self, user):
        collection = Collection().createCollection('Arbor',
                                                   creator=user,
                                                   public=True,
                                                   reuseExisting=True)

        Folder().createFolder(collection, 'Results',
                              parentType='collection',
                              public=True,
                              creator=user,
                              reuseExisting=True)

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
        anon_user = self._create_anonymous_user()
        self._create_result_folder(anon_user)
        getPlugin('jobs').load(info)
        info['apiRoot'].arbor_nova = rest.ArborNova()
