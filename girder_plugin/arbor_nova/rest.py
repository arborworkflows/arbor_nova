#!/usr/bin/env python
# -*- coding: utf-8 -*-

from arbor_nova_tasks.arbor_tasks.example import column_append
from arbor_nova_tasks.arbor_tasks.app_support import pgls
from arbor_nova_tasks.arbor_tasks.app_support import asr 
from arbor_nova_tasks.arbor_tasks.fnlcr import polyA_v10 
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
        self.route('POST', ('asr', ), self.asr)
        self.route('POST', ('polya', ), self.polyA_v10)

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


# added ASR from app_support directory

    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('ASR')
        .param('treeFileId', 'The ID of the input tree file.')
        .param('tableFileId', 'The ID of the input table file.')
        .param('selectedColumn', 'The character to use for calculation of ASR.')
        .param('resultSummaryItemId', 'The ID of the output item where the model summary file will be uploaded.')
        .param('plotItemId', 'The ID of the output item where the plot file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def asr(
        self,
        treeFileId,
        tableFileId,
        selectedColumn,
        resultSummaryItemId,
        plotItemId
    ):
        result = asr.delay(
            GirderFileId(treeFileId),
            GirderFileId(tableFileId),
            selectedColumn,
            girder_result_hooks=[
                GirderUploadToItem(resultSummaryItemId),
                GirderUploadToItem(plotItemId)
            ])

        return result.job

    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('Calculate a Polyadenylation (PolyA) tail')
        .param('fastaId', 'The ID of the input file.')
        .param('linkerId', 'The ID of the linker input file.')
        .param('transcriptId', 'The ID of the input file.')
        .param('outputId', 'The ID of the output item where the output file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def polyA_v10(
            self, 
            fastaId, 
            linkerId, 
            transcriptId,
            outputId
    ):
        result = polyA_v10.delay(
                GirderFileId(fastaId), 
                GirderFileId(linkerId),
                GirderFileId(transcriptId),
                girder_result_hooks=[
                    GirderUploadToItem(outputId)
                ])
        return result.job

