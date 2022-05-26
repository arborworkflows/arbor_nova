from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

import pandas as pd
import numpy as np
import os


# This routine allows selection of a dataset, it uses PANDAS to perform one of several selected correlation analyses, 
# and then returns the unrolled matrix, suitable for rendering using Vega-lite. 

#--------- support routines for processing TERRA-Ref season measurements ----------------



#-------------- end of support routines ----------------



@girder_job(title='TerraCorrelation')
@app.task(bind=True)
def terra_correlation(
    self,
    season,
    correlation,
    **kwargs
):

   # initialize with the proper season of data
    if (season == 'Season 4'):
        data_filename = 's4_height_and_models.csv'
    elif (season == 'Season 6'):
        data_filename = 's6_height_and_models.csv'
    elif (season == 'S4 Hand Measurements'):
        data_filename = 's4_august_by_hand_30plus_v2.csv'
    elif (season == 'S4 July Features'):
        data_filename = 's4july_traits_and_models.csv'
    else:
        print('unknown season');

    # the CyVerse discovery environment overwrites the user file system so user's data 
    # is always available.  Let's look for a preloaded dataset copy if the default local
    # one is not there

    de_path = '/data/work/shared/genophenoenvo/sorghum/terraVisualization' 
    path = '/arbor_nova/girder_worker_tasks/data'
    #path = '/arbor_nova'
    if os.path.isdir(path):
        print('reading local data file')
        traits_df = pd.read_csv(path+'/'+data_filename)
    else:
        print('reading shared data file')
        traits_df = pd.read_csv(de_path+'/'+data_filename)
    print('reading complete')

    # now see what correlation option was selected
    if (correlation == 'Kendall Tau Correlation'):
        correlation = 'kendall'
    elif (correlation == 'Spearman Rank Correlation'):
        correlation = 'spearman'
    else:
        correlation = 'pearson'


    # now perform the correlation analysis, unroll the result, and rename the columns
    corrMat = traits_df.corr(correlation).stack().reset_index()
    renamedMat = corrMat.rename(columns={0: 'correlation', 'level_0': 'variable', 'level_1': 'variable2'})

    
    # place the file in a temporary location so it is readable without a girder login
    outname = NamedTemporaryFile(delete=False).name+'.csv'
    renamedMat.to_csv(outname,index=False)
    print('output correlation data complete')
    return outname 
