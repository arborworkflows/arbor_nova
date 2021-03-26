#!/usr/bin/env python
# -*- coding: utf-8 -*-

from arbor_nova_tasks.arbor_tasks.example import column_append
from arbor_nova_tasks.arbor_tasks.app_support import pgls
from arbor_nova_tasks.arbor_tasks.app_support import asr 
#from arbor_nova_tasks.arbor_tasks.fnlcr import polyA_v10 
from arbor_nova_tasks.arbor_tasks.fnlcr import blastn 
from arbor_nova_tasks.arbor_tasks.fnlcr import infer 
from arbor_nova_tasks.arbor_tasks.fnlcr import docker_polyA 
from arbor_nova_tasks.arbor_tasks.fnlcr import infer_rhabdo 
from arbor_nova_tasks.arbor_tasks.fnlcr import infer_wsi 
from arbor_nova_tasks.arbor_tasks.fnlcr import wsi_thumbnail
from arbor_nova_tasks.arbor_tasks.fnlcr import request_gpu
from arbor_nova_tasks.arbor_tasks.fnlcr import release_gpu

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
        #self.route('POST', ('polya', ), self.polyA_v10)
        self.route('POST', ('docker_polya', ), self.docker_polyA)
        self.route('POST', ('blastn', ), self.blastn)
        self.route('POST', ('infer', ), self.infer)
        self.route('POST', ('infer_rhabdo', ), self.infer_rhabdo)
        self.route('POST', ('infer_wsi', ), self.infer_wsi)
        self.route('POST', ('wsi_thumbnail', ), self.wsi_thumbnail)
        self.route('POST', ('request_gpu', ), self.request_gpu)
        self.route('POST', ('release_gpu', ), self.release_gpu)

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

# --- polyA python3 script for FNLCR
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

# --- polyA executed via docker for FNLCR
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('Calculate a Polyadenylation (PolyA) tail (via Jacks docker image')
        .param('fastaId', 'The ID of the input file.')
        .param('linkerId', 'The ID of the linker input file.')
        .param('transcriptId', 'The ID of the input file.')
        .param('outputId', 'The ID of the output item where the output file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def docker_polyA(
            self, 
            fastaId, 
            linkerId, 
            transcriptId,
            outputId
    ):
        result = docker_polyA.delay(
                GirderFileId(fastaId), 
                GirderFileId(linkerId),
                GirderFileId(transcriptId),
                girder_result_hooks=[
                    GirderUploadToItem(outputId)
                ])
        return result.job

# --- blastn command line for FNLCR
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('run blastn to compare two fasta files')
        .param('fastaId', 'The ID of the source file.')
        .param('linkerId', 'The ID of the query file.')
        .param('outputId', 'The ID of the output item where the output file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def blastn(
            self, 
            fastaId, 
            linkerId, 
            outputId
    ):
        result = blastn.delay(
                GirderFileId(fastaId), 
                GirderFileId(linkerId),
                girder_result_hooks=[
                    GirderUploadToItem(outputId)
                ])
        return result.job

# ---DNN infer command line for FNLCR
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('perform forward inferencing using a pretrained network')
        .param('fastaId', 'The ID of the source, a numpy array file.')
        .param('outputId', 'The ID of the output item where the output file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def infer(
            self, 
            fastaId, 
            outputId
    ):
        result = infer.delay(
                GirderFileId(fastaId), 
                girder_result_hooks=[
                    GirderUploadToItem(outputId)
                ])
        return result.job

# ---DNN infer command line for FNLCR
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('perform forward inferencing using a pretrained network')
        .param('imageId', 'The ID of the source, a TIF image file.')
        .param('outputId', 'The ID of the output item where the output file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def infer_rhabdo(
            self, 
            imageId, 
            outputId
    ):
        result = infer_rhabdo.delay(
                GirderFileId(imageId), 
                girder_result_hooks=[
                    GirderUploadToItem(outputId)
                ])
        return result.job

        # ---DNN infer command line for FNLCR
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('perform forward inferencing using a pretrained network')
        .param('imageId', 'The ID of the source, an Aperio .SVS image file.')
        .param('outputId', 'The ID of the output item where the output file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def infer_wsi(
            self, 
            imageId, 
            outputId
    ):
        result = infer_wsi.delay(
                GirderFileId(imageId), 
                girder_result_hooks=[
                    GirderUploadToItem(outputId)
                ])
        return result.job

    # --- generate a thumbnail from a pyramidal image
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('generate a wsi_thumbnail')
        .param('imageId', 'The ID of the source, an Aperio .SVS image file.')
        .param('outputId', 'The ID of the output item where the output file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def wsi_thumbnail(
            self, 
            imageId, 
            outputId
    ):
        result = wsi_thumbnail.delay(
                GirderFileId(imageId), 
                girder_result_hooks=[
                    GirderUploadToItem(outputId)
                ])
        return result.job


    # --- generate a thumbnail from a pyramidal image
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('request a gpu')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def request_gpu(self):
        result = request_gpu.delay()
        return result.job


    # --- generate a thumbnail from a pyramidal image
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('return a currently allocated GPU')
        .param('gpuname', 'The ID of the device name ex "cuda0".')
        .param('status', 'The ID of the output item where the output file will be uploaded.')
        .errorResponse()
        .errorResponse('Write access was denied on the parent item.', 403)
        .errorResponse('Failed to upload output file.', 500)
    )
    def release_gpu(
            self,  
            gpuname
    ):
        result = release_gpu.delay(
              gpuname
            )
        return result.job
