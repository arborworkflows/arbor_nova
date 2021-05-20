from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
import warnings

#--------- support routines for processing TERRA-Ref season measurements ----------------


# define a method that receives a dataframe, runs a model, and appends columns
# containing the model values and errors to the original dataframe and returns the resulting
# dataframe for further processing into a visualization

def runXGBoostPerCultivarOnSeasonMeasurements(dataFrm,estimators=100,learningRate=0.1,maxDepth=8):
    gbr_models = {}
    predictions = {}
    list_of_counts = []
    count = 0
    grouped = dataFrm.groupby(['cultivar'])
    for name,group in grouped:
        #print(name)
        # pick the features to use for training
        train_df = group[['day_offset','range','column','leaf_angle_alpha','leaf_angle_beta','leaf_angle_chi','leaf_angle_mean']]
        # identify the 'target' feature to try to predict
        target_df = group['canopy_height']
        X_train = train_df.values
        y_train = target_df.values
        # record how many points were used for training
        countRec = {'cultivar': name, 'count': X_train.shape[0]}
        list_of_counts.append(countRec)
        # train a model for this cultivar in this location and store the trained model in a dictionary
        gbr_models[name] = GradientBoostingRegressor(
                                n_estimators=int(estimators),
                                learning_rate=float(learningRate),
                                max_depth=int(maxDepth),
                                random_state=0, loss='ls').fit(X_train, y_train)
        gbr_pred = gbr_models[name].predict(X_train)
        count += 1
        # add the model results back into the dataframe so we can plot the actual and predicted against all the indepedent variables
        train_df['per_cultivar_gboost'] = gbr_pred

        #put the actual target value back in the dataframe so we can plot results
        train_df['canopy_height'] = target_df

        # calculate the per measurement error
        train_df['abserror_per_cultivar_gboost'] = 100.0*abs(train_df['canopy_height']-train_df['per_cultivar_gboost'])/train_df['canopy_height']

        # store the predicted results in the same dictionary organization and the trained models
        predictions[name] = train_df
        if (count % 50) == 0:
            print('in process:',count, 'models')
    print('finished generating',count,'models')

    # A separate model was run for each cultivar, so the output 'predictions' is a dictionary
    # with the cultivar as the keys and all the measurements and predictions as separate
    # dataframes. First combine the multiple cultivar predictions into a single output
    # dataframe. Then, we can join with the main dataframe to add this model.

    firstTime = True
    # go through each cultivar
    for key in predictions.keys():
        this_df = predictions[key]
        # add cultivar name to measurements dataframe
        this_df['cultivar'] = key
        # calculate the average error across the season and add it to the output
        this_df['avg_error_per_cultivar_gboost'] = this_df['abserror_per_cultivar_gboost'].agg(np.mean)
        # now add these lines to the output
        if firstTime:
            per_cultivar_df = this_df
            firstTime = False
        else:
            per_cultivar_df = per_cultivar_df.append(this_df,ignore_index=True)

    # return the original dataframe augmented with the model values 
    return per_cultivar_df



#-------------- end of support routines ----------------





@girder_job(title='TerraPerCultivarModel')
@app.task(bind=True)
def terra_per_cultivar_model(
    self,
    season,
    estimators,
    depth,
    learn,
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

    path = '/arbor_nova/girder_worker_tasks/data'
    #path = '/home/vagrant/arbor_nova/girder_worker_tasks/arbor_nova_tasks/arbor_tasks/app_support'
    #print('reading data file')
    traits_df = pd.read_csv(path+'/'+data_filename)
    #print('reading complete')

    # The model generations runtime warnings so this suppresses the warnings
    warnings.filterwarnings(action='ignore')

    # run the extraction of the trait values across the field at or as soon before the reqested day as possible
    predict_df = runXGBoostPerCultivarOnSeasonMeasurements(
                traits_df, 
                estimators=estimators,
                maxDepth=depth,
                learningRate=learn)

    # re-enable runtime warnings in case we need them for debugging
    warnings.filterwarnings(action='once')

    # write out the model results, so they can be browsed by other endpoints
    predict_df.to_csv(path+'/'+'per_cultivar_model_output.csv',index=False)

    # place the file in a temporary location so it is readable without a girder login
    outname = NamedTemporaryFile(delete=False).name+'.csv'
    predict_df.to_csv(outname,index=False)
    print('model output writing complete')
    #print('terra_daily_trait filename:',outname )
    return outname 
