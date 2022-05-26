from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

import pandas as pd
import numpy as np

#--------- support routines for processing TERRA-Ref season measurements ----------------



#-------------- end of support routines ----------------



@girder_job(title='TerraOneCultivar')
@app.task(bind=True)
def terra_one_cultivar(
    self,
    season,
    cultivar,
    **kwargs
):

    # initialize with the proper season of data
    if (season == 'Season 4'):
        data_filename = 's4_height_and_models.csv'
    elif (season == 'Season 6'):
        data_filename = 's6_height_and_models.csv'
    else:
        print('unknown season');

    path = '/arbor_nova/girder_worker_tasks/data'
    de_path = '/cyverse/work/home/shared/genophenoenvo/data/sorghum/terraVisualization' 

    if os.path.isdir(path):
        print('reading local data file')
        traits_df = pd.read_csv(path+'/'+data_filename)
    else:
        print('reading shared data file')
        traits_df = pd.read_csv(de_path+'/'+data_filename)
    print('reading complete')

    # filter for measurements of only one cultivar
    filter_df = traits_df.loc[traits_df['cultivar'] == cultivar]

    # place the file in a temporary location so it is readable without a girder login
    outname = NamedTemporaryFile(delete=False).name+'.csv'
    filter_df.to_csv(outname,index=False)
    print('output one cultivar data complete')
    return outname 
