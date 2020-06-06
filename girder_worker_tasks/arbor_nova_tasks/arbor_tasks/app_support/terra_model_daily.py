from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

import girder_client

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
import json

#--------- support routines for processing TERRA-Ref season measurements ----------------


def addPlotMarker(plotlist,cultivar,rng,column,selectedFeatureName,featureValue,day):
    mark = {}
    mark['cultivar'] = cultivar
    mark['range'] = rng
    mark['column'] = column
    mark['day'] = day
    mark[selectedFeatureName] = featureValue
    plotlist.append(mark)

# this method takes an input day of the season and generates an output dataframe with the most recent
#  measurement of a selectedFeature taken for each location in the field.  It is a way to watch the field develop
# over time during the season.

def renderFeatureOnDay(dataFrm, selectedDay,selectedFeature):
    summary_df = dataFrm.describe()
    minColumn = summary_df.loc['min','column']
    minRange =  summary_df.loc['min','range']
    maxColumn = summary_df.loc['max','column']
    maxRange =  summary_df.loc['max','range']

    # if it is a string value, change the string to an integer
    selectedDay = int(selectedDay)

    # first get rid of observations after the query day
    before_df = dataFrm.loc[dataFrm['day_offset'] <= selectedDay]
    print(before_df.shape)

    # group all the measurements so far by cultivar
    grouped = before_df.groupby(['range','column'])

    # now loop through these by cultivar and select only the measurement with the highest day_offset value (the most recent)
    recentlist = []
    for name, group in grouped:
        #print(name)
        selected = group['day_offset'].idxmax()  # this selects the highest value index
        # the index is a lookup into the original dataframe, so put this entry in the list for plotting
        recentlist.append(dataFrm.iloc[selected])

    # how many cultivars did we find that had a measurement on or before our day?
    print(len(recentlist),"cultivars have been measured on or before day",selectedDay)
    recent_df = pd.DataFrame(recentlist)

    # now fill out the entire field by querying the values at each location from the
    # recent dataframe and filling in a plotting list.  This global list (plotlist) needs to be empty
    # before running this algorithm.

    plotlist = []
    cultivarCount = 0
    measurementCount = 0
    # go once across the entire field by using range and column indices
    for rng in range(int(minRange),int(maxRange+1)):
        for col in range(int(minColumn),int(maxColumn+1)):
            # find which cultivar is in this spot in the field
            CultivarListInThisSpot = dataFrm.loc[(dataFrm['range'] == rng) & (dataFrm['column']==col)]['cultivar']
            print
            # return a Series of the cultivar names. If the square isn't empty, get the cultivar name from the list.
            # all cultivar names should be identical since we have selected multiple measurements (on different days) from the same location
            if len(CultivarListInThisSpot)> 0:
                cultivarCount += 1
                thisCultivar = CultivarListInThisSpot.values[0]
                # catch exception because recent_df might be empty if day requested is before all measurments
                try:
                    thisMeasurement = recent_df.loc[(recent_df['range'] == rng) & (recent_df['column'] == col)][selectedFeature]
                    thisMeasurementDay = recent_df.loc[(recent_df['range'] == rng) & (recent_df['column'] == col)]['day_offset']

                    # depending on the day, we might or might not have had a previous measurement, so check there was a measurement
                    # before plotting.  This filter prevents a run-time error trying to plot non-existent measurements.  See the
                    # "else" case below for when there is no previous measurement.
                    if len(thisMeasurement)>0:
                        measurementCount += 1
                        thisMeasurementValue = thisMeasurement.values[0]
                        thisMeasurementDayValue = thisMeasurementDay.values[0]
                        addPlotMarker(plotlist,thisCultivar,rng,col,selectedFeature,thisMeasurementValue,thisMeasurementDayValue)
                    else:
                        # fill in empty entries for locations where there were no measurements. This happens more during
                        # the early part of the season because measurements haven't been taken in some locations yet. This
                        # way, the plot will always render the full field because all locations will have an entry, even
                        # if it is zero because no measurements have been taken yet.
                        addPlotMarker(plotlist,thisCultivar,rng,col,selectedFeature,0.0,0)
                except:
                    # support the case where the date was so low, there were no measurements at all
                    addPlotMarker(plotlist,thisCultivar,rng,col,selectedFeature,0.0,0)

    plotdf = pd.DataFrame(plotlist)
    #print('cultivars found:',cultivarCount)
    #print('measurements found:',measurementCount)
    #print('plotted',len(plotlist),'values')
    return plotdf


#-------------- end of support routines ----------------





@girder_job(title='TerraModelDaily')
@app.task(bind=True)
def terra_model_daily(
    self,
    selectedDay,
    selectedTrait,
    modelResultId,
    **kwargs
):

    # ToDo: read the modelId item number and retrieve the particular model from Girder. This way multiple
    # users can access the app simultaneously without over-writing each other.  In the meantime, we 
    # will read a previously-written file on the server. 

    print('received girder model Id:',modelResultId)
    # ToDo: future use of girder
    # import girder-client
    # login to girder
    # model = girderRestApi(get file attached to item by id)

    gc = girder_client.GirderClient(apiUrl='http://localhost:8080/girder/api/v1')
    login = gc.authenticate('anonymous', 'letmein')
    filelist = []
    for fileobj in gc.listFile(modelResultId):
       filelist.append(fileobj['name']) 
    firstfilename = filelist[0]
    print('recovered model filename:',firstfilename)
    fullfilepath = '/tmp/'+firstfilename

    # initialize with the output of the model 
    #path = '/home/vagrant/arbor_nova/girder_worker_tasks/arbor_nova_tasks/arbor_tasks/app_support'
    #data_filename = 'per_cultivar_model_output.csv'
    #path = '.'
    #fullfilepath = path+'/'+data_filename
    print('reading model output file: ',fullfilepath)
    traits_df = pd.read_csv(fullfilepath)

    # Didn't work because of size of request: 
    # instead of being read from a file, the data is passed live through the HTTP link, so multiple 
    # users can run models simultaneously without interfering with each other (through file overwriting).
    #print('reading model results ')
    #modelResults = json.loads(modelResults)
    #print('type:',type(modelResults))
    #print('modelResults:',modelResults)
    #traits_df = modelResults['data'] 

    # we are passing back the model results, so convert them to a dataframe for use
    #print('processing model data')
    #traits_df = pd.DataFrame(modelResults)
    #print('completed.')

    # run the extraction of the trait values across the field at or as soon before the reqested day as possible
    result_df = renderFeatureOnDay(
                traits_df,
                selectedDay,
                selectedTrait)

    # place the file in a temporary location so it is readable without a girder login
    outname = NamedTemporaryFile(delete=False).name+'.csv'
    result_df.to_csv(outname,index=False)
    print('writing daily complete')
    #print('terra_daily_trait filename:',outname )
    return outname 
