from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

import pandas as pd
import numpy as np

#--------- support routines for processing TERRA-Ref season measurements ----------------



#-------------- end of support routines ----------------



@girder_job(title='TerraSeason')
@app.task(bind=True)
def terra_season(
    self,
    season,
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

    #path = '/home/vagrant/arbor_nova/girder_worker_tasks/arbor_nova_tasks/arbor_tasks/app_support'
    path = '/arbor_nova/girder_worker_tasks/data'
    #print('reading data file')
    traits_df = pd.read_csv(path+'/'+data_filename)
    #print('reading complete')

    # place the file in a temporary location so it is readable without a girder login
    outname = NamedTemporaryFile(delete=False).name+'.csv'
    traits_df.to_csv(outname,index=False)
    print('output season data complete')
    return outname 
