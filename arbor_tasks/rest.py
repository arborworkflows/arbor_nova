#!/usr/bin/env python
# -*- coding: utf-8 -*-


from arbor_gw_tasks import column_append
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import filtermodel, Resource
from girder.models.token import Token
from girder_worker_utils.transforms import girder_io


class ArborTask(Resource):
    def __init__(self):
        super(ArborTask, self).__init__()
        self.resourceName = 'arbor_task'
        self.route('POST', ('csvColumnAppend', ), self.csv_column_append)

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
        token = Token().createToken(user=self.getCurrentUser())
        token_id = str(token['_id'])
        result = column_append.delay(in_filepath=girder_io.GirderFileId(fileId),
                                     output_item_id=itemId,
                                     girder_client_token=token_id)

        return result.job
