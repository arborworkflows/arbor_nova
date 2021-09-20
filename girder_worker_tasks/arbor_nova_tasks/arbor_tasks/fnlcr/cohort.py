
# added for girder interaction as plugin arbor task
from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile
import pandas as pd


@girder_job(title='cohort')
@app.task(bind=True)
def cohort(
    self,
    cohortName
):

   # initialize with the proper season of data
    print('received cohort selection:',cohortName)
    if (cohortName == 'myod1'):
        data_filename = 'rms_myod1_cohort.csv'
    elif (cohortName == 'survivability'):
        data_filename = 'rms_survivability_cohort.csv'
    else:
        print('unknown cohort')

    path = './data'
    print('reading data file')
    cohort_df = pd.read_csv(path+'/'+data_filename)
    print('reading complete')

    # place the file in a temporary location so it is readable without a girder login
    outname = NamedTemporaryFile(delete=False).name+'.csv'
    cohort_df.to_csv(outname,index=False)
    print('return cohort data complete')
    return outname 