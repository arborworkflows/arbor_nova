from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

import pandas as pd

@girder_job(title='TerraSchema')
@app.task(bind=True)
def terra_schema(
    self,
    **kwargs
):

    # this is a mini version of the data file that is quick to read and write here
    schema_filename = 's4_schema.csv'
    path = '.'
    path = '/home/vagrant/arbor_nova/girder_worker_tasks/arbor_nova_tasks/arbor_tasks/app_support'
    print('reading data file')
    traits_df = pd.read_csv(path+'/'+schema_filename)
    print('reading complete')
    # place the file in a temporary location so it is readable without a girder login
    outname = NamedTemporaryFile(delete=False).name+'.csv'
    traits_df.to_csv(outname,index=False)
    print('writing complete')
    print('terra_schema filename:',outname )
    return outname 