#!/usr/bin/env python
# -*- coding: utf-8 -*-

from arbor_nova_tasks.arbor_tasks.example import column_append
from arbor_nova_tasks.arbor_tasks.app_support import pgls
from arbor_nova_tasks.arbor_tasks.app_support import asr 
from arbor_nova_tasks.arbor_tasks.app_support import phylosignal 
from arbor_nova_tasks.arbor_tasks.app_support import fitdiscrete 
from arbor_nova_tasks.arbor_tasks.app_support import fitcontinuous
from arbor_nova_tasks.arbor_tasks.app_support import pic 
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
        self.route('POST', ('phylosignal', ), self.phylosignal)
        self.route('POST', ('fitdiscrete', ), self.fitdiscrete)
        self.route('POST', ('fitcontinuous', ), self.fitcontinuous)
        self.route('POST', ('pic', ), self.pic)

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


# added PhyloSignal from app_support directory

    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('phylosignal')
        .param('treeFileId', 'The ID of the input tree file.')
        .param('tableFileId', 'The ID of the input table file.')
        .param('selectedColumn', 'The character to use for calculation of phylosginal.')
        .param('method', 'The method used for calculation.')
	.param('selectedDiscrete', 'The Discrete model type to use for calculation.')
        .param('resultSummaryItemId', 'The ID of the output item where the model summary file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def phylosignal(
        self,
        treeFileId,
        tableFileId,
        selectedColumn,
        method,
	selectedDiscrete,
        resultSummaryItemId
    ):
        result = phylosignal.delay(
            GirderFileId(treeFileId),
            GirderFileId(tableFileId),
            selectedColumn,
            method,
	    selectedDiscrete,
            girder_result_hooks=[
                GirderUploadToItem(resultSummaryItemId)
            ])
        return result.job


# added FitDiscrete from app_support directory
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('fitdiscrete')
        .param('treeFileId', 'The ID of the input tree file.')
        .param('tableFileId', 'The ID of the input table file.')
        .param('selectedColumn', 'The character to use for calculation of phylosginal.')
        .param('model', 'The model to fit to the data.')
	.param('selectedTransformation', 'The evolutionary model used to transform the tree.')
        .param('resultSummaryItemId', 'The ID of the output item where the model summary file will be uploaded.')
        .param('plotItemId', 'The ID of the output item where the plot file will be uploaded')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def fitdiscrete(
        self,
        treeFileId,
        tableFileId,
        selectedColumn,
        model,
	selectedTransformation,
        resultSummaryItemId,
	plotItemId
    ):
        result = fitdiscrete.delay(
            GirderFileId(treeFileId),
            GirderFileId(tableFileId),
            selectedColumn,
            model,
	    selectedTransformation,
            girder_result_hooks=[
                GirderUploadToItem(resultSummaryItemId),
		GirderUploadToItem(plotItemId)
            ])
        return result.job
   
# added FitContinuous from app_support directory
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('fitcontinuous')
        .param('treeFileId', 'The ID of the input tree file.')
        .param('tableFileId', 'The ID of the input table file.')
        .param('selectedColumn', 'The character to use for calculation.')
        .param('model', 'The model to use for calculation.')
	.param('stdError', 'The standard error to use for calculation.')
        .param('resultSummaryItemId', 'The ID of the output item where the model summary file will be uploaded.')
        .param('plotItemId', 'The ID of the output item where the plot file will be saved')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def fitcontinuous(
        self,
        treeFileId,
        tableFileId,
        selectedColumn,
        model,
	stdError,
        resultSummaryItemId,
	plotItemId
    ):
        result = fitcontinuous.delay(
            GirderFileId(treeFileId),
            GirderFileId(tableFileId),
            selectedColumn,
            model,
	    stdError,
            girder_result_hooks=[
                GirderUploadToItem(resultSummaryItemId),
		GirderUploadToItem(plotItemId)
            ])
        return result.job

# added PIC from app_support directory
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('PIC')
        .param('treeFileId', 'The ID of the input tree file.')
        .param('tableFileId', 'The ID of the input table file.')
        .param('independentVariable', 'The independent variable for use in calculation.')
        .param('dependentVariable', 'The dependent variable for use in calculation.')
        .param('resultSummaryItemId', 'The ID of the output item where the model summary file will be uploaded.')
        .param('plotItemId', 'The ID of the output item where the plot file will be saved')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def pic(
        self,
        treeFileId,
        tableFileId,
        independentVariable,
        dependentVariable,
        resultSummaryItemId,
	plotItemId
    ):
        result = pic.delay(
            GirderFileId(treeFileId),
            GirderFileId(tableFileId),
            independentVariable,
            dependentVariable,
            girder_result_hooks=[
                GirderUploadToItem(resultSummaryItemId),
		GirderUploadToItem(plotItemId)
            ])
        return result.job
