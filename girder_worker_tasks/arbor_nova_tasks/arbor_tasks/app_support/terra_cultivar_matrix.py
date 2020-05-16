from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
import warnings

#--------- support routines for processing TERRA-Ref season measurements ----------------


def generateCultivarMatrix(dataFrm,count=25,trait='canopy_height',operation='max'):
    grouped = dataFrm.groupby(['cultivar'])
    error = False

    # in case we are passed the count as a string
    count = int(count)

    # group the data according to cultivar and aggregate the selected trait value according to the selected
    # parameter.  We are generating a new dataframe with a single value of the trait for each cultivar.
    plotlist = []
    for name,group in grouped:
        mark = {}
        mark['cultivar'] = name
        if (operation == 'max'):
            mark[trait] = group[trait].agg(np.max)
        elif (operation == 'min'):
            mark[trait] = group[trait].agg(np.min)
        elif (operation == 'mean'):
            mark[trait] = group[trait].agg(np.mean)
        elif (operation == 'avg'):
            mark[trait] = group[trait].agg(np.mean)
        else:
            error = True
            break
        plotlist.append(mark)
    if error:
        print('error - invalid operation type in predictCultivarMatrix');
    cultivars_df = pd.DataFrame(plotlist)

    # we made one entry for each cultivar
    cultivar_count = len(plotlist)

    # don't let the sample be larger than the whole dataset, clamp at the dataset size. 
    # we offer to downsample the dataset to allow dataset exploration at lower cost. 
    sampleSize = min(count,cultivar_count) 
    cultivars = cultivars_df.sample(sampleSize)['cultivar']

    # now loop through the cultivars and calculate the difference in the trait value
    # for each pairwise difference.  This will require  sampleSize^2 time
    plotlist = []
    for cult in cultivars:
        cult1value = (cultivars_df.loc[cultivars_df['cultivar']==cult][trait])
        for cult2 in cultivars:
            cult2value = (cultivars_df.loc[cultivars_df['cultivar']==cult2][trait])
            #print(cult2height)
            #print(cult2height[1])
            mark = {}
            mark['cultivar1'] = cult
            mark['cultivar2'] = cult2
            mark['difference'] = abs(cult1value.iloc[0] - cult2value.iloc[0])
            plotlist.append(mark)

    # return the answer as a dataframe
    plot_df = pd.DataFrame(plotlist)
    return plot_df



#-------------- end of support routines ----------------





@girder_job(title='TerraCultivarMatrix')
@app.task(bind=True)
def terra_cultivar_matrix(
    self,
    season,
    count,
    trait,
    **kwargs
):


    # initialize with the proper season of data
    if (season == 'Season 4'):
        data_filename = 's4_height_and_models.csv'
    elif (season == 'Season 6'):
        data_filename = 's6_height_and_models.csv'
    else:
        print('unknown season');

    path = '/home/vagrant/arbor_nova/girder_worker_tasks/arbor_nova_tasks/arbor_tasks/app_support'
    #print('reading data file')
    traits_df = pd.read_csv(path+'/'+data_filename)
    #print('reading complete')

    # run the extraction of the trait values across the field at or as soon before the reqested day as possible
    predict_df = generateCultivarMatrix(
                traits_df, 
                count=count,
                trait=trait,
                operation='max')

    # write out the model results, so they can be browsed by other endpoints
    predict_df.to_csv(path+'/'+'per_cultivar_model_output.csv',index=False)

    # place the file in a temporary location so it is readable without a girder login
    outname = NamedTemporaryFile(delete=False).name+'.csv'
    predict_df.to_csv(outname,index=False)
    print('cultivar matrix output writing complete')
    return outname 
