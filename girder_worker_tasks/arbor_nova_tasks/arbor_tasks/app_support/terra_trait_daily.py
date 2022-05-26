from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

import pandas as pd

import os


#--------- support routines for processing TERRA-Ref season measurements ----------------


def addPlotMarker(plotlist,cultivar,rng,column,selectedFeatureName,featureValue):
    mark = {}
    mark['cultivar'] = cultivar
    mark['range'] = rng
    mark['column'] = column
    mark[selectedFeatureName] = featureValue
    plotlist.append(mark)

# this method takes an input day of the season and generates an output dataframe with the most recent
#  measurement of a selectedFeature taken for each location in the field.  It is a way to watch the field develop
# over time during the season.

def renderCanopyHeightOnDay(dataFrm, minRange,minColumn, maxRange, maxColumn, selectedDay,selectedFeature):

    # accumulate matching measturements here
    plotlist = []

    # first get rid of observations after the query day
    before_df = dataFrm.loc[dataFrm['day_offset'] <= selectedDay]
    #print(before_df.shape)

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
    #print(len(recentlist),"cultivars have been measured on or before day",selectedDay)
    recent_df = pd.DataFrame(recentlist)

    # now fill out the entire field by querying the values at each location from the
    # recent dataframe and filling in a plotting list.  This parameter list (plotlist) needs to be empty
    # before running this algorithm.

    cultivarCount = 0
    measurementCount = 0
    # go once across the entire field by using range and column indices
    for rng in range(int(minRange),int(maxRange+1)):
        for col in range(int(minColumn),int(maxColumn+1)):
            #print(rng,col)
            # find which cultivar is in this spot in the field
            CultivarListInThisSpot = dataFrm.loc[(dataFrm['range'] == rng) & (dataFrm['column']==col)]['cultivar']
            # return a Series of the cultivar names. If the square isn't empty, get the cultivar name from the list.
            # all cultivar names should be identical since we have selected multiple measurements (on different days) from the same location
            if len(CultivarListInThisSpot)> 0:
                cultivarCount += 1
                thisCultivar = CultivarListInThisSpot.values[0]
                # if too early a day is picked, there might be no measurements, so catch this case and return zero
                try:
                    thisMeasurement = recent_df.loc[(recent_df['range'] == rng) & (recent_df['column'] == col)][selectedFeature]
                    # depending on the day, we might or might not have had a previous measurement, so check there was a measurement
                    # before plotting.  This filter prevents a run-time error trying to plot non-existent measurements.  See the
                    # "else" case below for when there is no previous measurement.
                    if len(thisMeasurement)>0:
                        measurementCount += 1
                        thisMeasurementValue = thisMeasurement.values[0]
                        addPlotMarker(plotlist,thisCultivar,rng,col,selectedFeature,thisMeasurementValue)
                    else:
                        # fill in empty entries for locations where there were no measurements. This happens more during
                        # the early part of the season because measurements haven't been taken in some locations yet. This
                        # way, the plot will always render the full field because all locations will have an entry, even
                        # if it is zero because no measurements have been taken yet.
                        addPlotMarker(plotlist,thisCultivar,rng,col,selectedFeature,0.0)
                except:
                    # return zero in the case there were no actual measurements yet, so empty plot can be drawn
                    addPlotMarker(plotlist,thisCultivar,rng,col,selectedFeature,0.0)


    plotdf = pd.DataFrame(plotlist)
    #print('cultivars found:',cultivarCount)
    print('measurements found:',measurementCount)
    #print('plotted',len(plotlist),'values')
    return plotdf


#-------------- end of support routines ----------------






@girder_job(title='TerraTraitDaily')
@app.task(bind=True)
def terra_trait_daily(
    self,
    season,
    selectedDay,
    selectedTrait,
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
    de_path = '/cyverse/work/home/shared/genophenoenvo/data/sorghum/terraVisualization' 
 
    if os.path.isdir(path):
        print('reading local data file')
        traits_df = pd.read_csv(path+'/'+data_filename)
    else:
        print('reading shared data file')
        traits_df = pd.read_csv(de_path+'/'+data_filename)
    print('reading complete')

    
    # find the field boundaries of the data dynamically.  It would be faster to hardcode this
    summary_df = traits_df.describe()
    minColumn = summary_df.loc['min','column']
    minRange =  summary_df.loc['min','range']
    maxColumn = summary_df.loc['max','column']
    maxRange =  summary_df.loc['max','range']

    # run the extraction of the trait values across the field at or as soon before the reqested day as possible
    plotdf = renderCanopyHeightOnDay(traits_df,minRange,minColumn,maxRange,maxColumn,float(selectedDay),selectedTrait)    

    # place the file in a temporary location so it is readable without a girder login
    outname = NamedTemporaryFile(delete=False).name+'.csv'
    plotdf.to_csv(outname,index=False)
    #print('writing complete')
    #print('terra_daily_trait filename:',outname )
    return outname 
