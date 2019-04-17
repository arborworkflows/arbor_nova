#!/usr/bin/env python
# -*- coding: utf-8 -*-


from arbor_nova_tasks import column_append
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import filtermodel, Resource
from girder.models.folder import Folder
from girder.models.item import Item
from girder_worker_utils.transforms.girder_io import GirderFileId, GirderUploadToItem


class ArborNova(Resource):
    def __init__(self):
        super(ArborNova, self).__init__()
        self.resourceName = 'arbor_nova'
        self.route('POST', ('csvColumnAppend', ), self.csv_column_append)

    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('Append a new column to a csv file.')
        .param('fileId', 'The ID of the input file.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def csv_column_append(self, fileId):
        result_folder = Folder().findOne({
            'name': 'Results'
        })
        item = Item().createItem('{}-{}'.format(self.resourceName, fileId),
                                 creator=self.getCurrentUser(),
                                 folder=result_folder)
        itemId = str(item['_id'])
        result = column_append.delay(GirderFileId(fileId),
                                     girder_result_hooks=[GirderUploadToItem(itemId)])

        return result.job
