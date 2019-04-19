#!/usr/bin/env python
# -*- coding: utf-8 -*-


from arbor_nova_tasks import column_append, pgls
from girder.api import access
from girder.api.describe import Description, autoDescribeRoute
from girder.api.rest import filtermodel, Resource
from girder_worker_utils.transforms.girder_io import GirderFileId, GirderUploadToItem


class ArborNova(Resource):
    def __init__(self):
        super(ArborNova, self).__init__()
        self.resourceName = 'arbor_nova'
        self.route('POST', ('csvColumnAppend', ), self.csv_column_append)
        self.route('POST', ('pgls', ), self.pgls)

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

    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('PGLS')
        .param('treeFileId', 'The ID of the input tree file.')
        .param('tableFileId', 'The ID of the input table file.')
        .param('correlation', 'The correlation mode.')
        .param('independentVariable', 'The independent variable.')
        .param('dependentVariable', 'The dependent variable.')
        .param('modelFitSummaryItemId', 'The ID of the output item where the model summary file will be uploaded.')
        .param('plotItemId', 'The ID of the output item where the plot file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def pgls(
        self,
        treeFileId,
        tableFileId,
        correlation,
        independentVariable,
        dependentVariable,
        modelFitSummaryItemId,
        plotItemId
    ):
        result = pgls.delay(
            GirderFileId(treeFileId),
            GirderFileId(tableFileId),
            correlation,
            independentVariable,
            dependentVariable,
            girder_result_hooks=[
                GirderUploadToItem(modelFitSummaryItemId),
                GirderUploadToItem(plotItemId)
            ])

        return result.job
