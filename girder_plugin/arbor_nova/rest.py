#!/usr/bin/env python
# -*- coding: utf-8 -*-

from arbor_nova_tasks.arbor_tasks.example import column_append
from arbor_nova_tasks.arbor_tasks.app_support import pgls
from arbor_nova_tasks.arbor_tasks.app_support import asr 
from arbor_nova_tasks.arbor_tasks.app_support import terra_schema
from arbor_nova_tasks.arbor_tasks.app_support import terra_trait_daily
from arbor_nova_tasks.arbor_tasks.app_support import terra_per_cultivar_model
from arbor_nova_tasks.arbor_tasks.app_support import terra_model_daily
from arbor_nova_tasks.arbor_tasks.app_support import terra_season
from arbor_nova_tasks.arbor_tasks.app_support import terra_cultivar_matrix
from arbor_nova_tasks.arbor_tasks.app_support import terra_one_cultivar
from arbor_nova_tasks.arbor_tasks.app_support import terra_selected_cultivars

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
        self.route('POST', ('terraSchema', ), self.terra_csv_schema)
        self.route('POST', ('terraTraitDaily', ), self.terra_csv_trait_daily)
        self.route('POST', ('terraModelDaily', ), self.terra_csv_model_daily)
        self.route('POST', ('terraPerCultivarModel', ), self.terra_csv_per_cultivar_model)
        self.route('POST', ('terraSeason', ), self.terra_season)
        self.route('POST', ('terraCultivarMatrix', ), self.terra_cultivar_matrix)
        self.route('POST', ('terraOneCultivar', ), self.terra_one_cultivar)
        self.route('POST', ('terraSelectedCultivars', ), self.terra_selected_cultivars)

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
        Description('TerraSchema')
        .param('outnameId', 'The ID of the output item where the schema file will be uploaded.')
        .errorResponse()
        .errorResponse('Terra_schema permission problem.', 403)
        .errorResponse('Terra_schema internal error',500)
    )
    def terra_csv_schema(
        self,
        outnameId
    ):
        result = terra_schema.delay(
            girder_result_hooks=[
                GirderUploadToItem(outnameId)
            ])
        return result.job


    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('TerraTraitDaily')
        .param('season', 'select which season to explore (string name, e.t. "Season 6").')
        .param('selectedDay', 'The day of the growing season selected for observation.')
        .param('selectedTrait', '(string) The name of the trait to return for that day. (e.g."canopy_heigth")') 
        .param('outnameId', 'The ID of the output item where the data file will be uploaded.')
        .errorResponse()
        .errorResponse('Terra_daily permission problem.', 403)
        .errorResponse('Terra_daily internal error',500)
    )
    def terra_csv_trait_daily(
        self,
        season,
        selectedDay,
        selectedTrait,
        outnameId
    ):
        result = terra_trait_daily.delay(
            season,
            selectedDay, 
            selectedTrait,
            girder_result_hooks=[
                GirderUploadToItem(outnameId)
            ])
        return result.job


    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('TerraModelDaily')
        .param('selectedDay', 'The day of the growing season selected for observation.')
        .param('selectedTrait', '(string) The name of the trait to return for that day. (e.g."canopy_heigth")') 
        .param('modelResults', 'a list of dictionaries that represent the model results')
        .param('outnameId', 'The ID of the output item where the data file will be uploaded.')
        .errorResponse()
        .errorResponse('Terra_daily permission problem.', 403)
        .errorResponse('Terra_daily internal error',500)
    )
    def terra_csv_model_daily(
        self,
        selectedDay,
        selectedTrait,
        modelResults,
        outnameId
    ):
        result = terra_model_daily.delay(
            selectedDay, 
            selectedTrait,
            modelResults,
            girder_result_hooks=[
                GirderUploadToItem(outnameId)
            ])
        return result.job



    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('TerraPerCultivarModel')
        .param('season', 'The season to model growth for') 
        .param('estimators', 'How many estimators to use in the XGBoost model.')
        .param('depth', 'How many decisions deep to investigate each option in XGBoost') 
        .param('learn', 'what learning rate to use for the XGBoost algorithm') 
        .param('outnameId', 'The ID of the output item where the data file will be uploaded.')
        .errorResponse()
        .errorResponse('Terra_daily permission problem.', 403)
        .errorResponse('Terra_daily internal error',500)
    )
    def terra_csv_per_cultivar_model(
        self,
        season,
        estimators,
        depth,
        learn,
        outnameId
    ):
        result = terra_per_cultivar_model.delay(
            season, 
            estimators,
            depth,
            learn,
            girder_result_hooks=[
                GirderUploadToItem(outnameId)
            ])
        return result.job


    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('TerraSeason')
        .param('season', 'The season to model growth for') 
        .param('outnameId', 'The ID of the output item where the data file will be uploaded.')
        .errorResponse()
        .errorResponse('Terra_season permission problem.', 403)
        .errorResponse('Terra_season internal error',500)
    )
    def terra_season(
        self,
        season,
        outnameId
    ):
        result = terra_season.delay(
            season, 
            girder_result_hooks=[
                GirderUploadToItem(outnameId)
            ])
        return result.job


    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('TerraCultivarMatrix')
        .param('season', 'The season to model growth for') 
        .param('count', 'How many cultivars to include in the output (up to dataset size)') 
        .param('trait', 'what trait should be displayed in the cultivar x cultivar matrix?') 
        .param('outnameId', 'The ID of the output item where the data file will be uploaded.')
        .errorResponse()
        .errorResponse('Terra_cultivar_matrix permission problem.', 403)
        .errorResponse('Terra_cultivar_matrix internal error',500)
    )
    def terra_cultivar_matrix(
        self,
        season,
        count,
        trait,
        outnameId
    ):
        result = terra_cultivar_matrix.delay(
            season, 
            count,
            trait,
            girder_result_hooks=[
                GirderUploadToItem(outnameId)
            ])
        return result.job


    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('TerraOneCultivar')
        .param('season', 'The season report') 
        .param('cultivar', 'The name of the single cultivar to return data for)') 
        .param('outnameId', 'The ID of the output item where the data file will be uploaded.')
        .errorResponse()
        .errorResponse('Terra_one_cultivar permission problem.', 403)
        .errorResponse('Terra_one_cultivar internal error',500)
    )
    def terra_one_cultivar(
        self,
        season,
        cultivar,
        outnameId
    ):
        result = terra_one_cultivar.delay(
            season, 
            cultivar,
            girder_result_hooks=[
                GirderUploadToItem(outnameId)
            ])
        return result.job

    
    @access.token
    @filtermodel(model='job', plugin='jobs')
    @autoDescribeRoute(
        Description('TerraSelectCultivars')
        .param('season', 'The season report') 
        .param('cultivar', 'A list of cultivar names to return data for)') 
        .param('outnameId', 'The ID of the output item where the data file will be uploaded.')
        .errorResponse()
        .errorResponse('Terra_selected_cultivar permission problem.', 403)
        .errorResponse('Terra_selected_cultivar internal error',500)
    )
    def terra_selected_cultivars(
        self,
        season,
        cultivar,
        outnameId
    ):
        result = terra_selected_cultivars.delay(
            season, 
            cultivar,
            girder_result_hooks=[
                GirderUploadToItem(outnameId)
            ])
        return result.job
