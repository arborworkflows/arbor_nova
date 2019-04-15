#!/usr/bin/env python
# -*- coding: utf-8 -*-


from arbor_nova_tasks import column_append
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import filtermodel, Resource, setCurrentUser
from girder.models.user import User
from girder_worker_utils.transforms.girder_io import GirderFileId, GirderUploadToItem


class ArborNova(Resource):
    def __init__(self, anonymous_user):
        super(ArborNova, self).__init__()
        self.resourceName = 'arbor_nova'
        self.route('POST', ('csvColumnAppend', ), self.csv_column_append)
        self.route('POST', ('anonlogin',), self.anonymousLogin)
        self.anonymous_user = anonymous_user

    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('Append a new column to a csv file.')
        .param('fileId', 'The ID of the input file.')
        .param('itemId', 'The ID of the output item where the output file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def csv_column_append(self, fileId, itemId):
        result = column_append.delay(GirderFileId(fileId),
                                     girder_result_hooks=[GirderUploadToItem(itemId)])

        return result.job

    @autoDescribeRoute(
        Description('Log in using the "anonymous user".')
    )
    @access.public
    def anonymousLogin(self, params):
        """Log in using the "anonymous user"."""
        user = User().findOne({
            'login': self.anonymous_user
        })
        user = User().filter(user, user)

        setCurrentUser(user)
        token = self.sendAuthTokenCookie(user)

        return {
            'user': user,
            'authToken': {
                'token': token['_id'],
                'expires': token['expires'],
                'scope': token['scope']
            },
            'message': 'Anonymous login succeeded.'
        }
