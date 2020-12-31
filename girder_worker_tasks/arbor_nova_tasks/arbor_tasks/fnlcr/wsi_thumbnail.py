# added for girder interaction as plugin arbor task
from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

import large_image

#-------------------------------------------

@girder_job(title='WSI-thumbnail')
@app.task(bind=True)
def wsi_thumbnail(self,image_file,**kwargs):

   
    print('generate a thumbnail for a WSI')
    # open an access handler on the large image
    source = large_image.getTileSource(image_file)
    # generate unique names for multiple runs.  Add extension so it is easier to use
    outname = NamedTemporaryFile(delete=False).name+'.png'

    thumbnail, mimeType = source.getThumbnail(
        width=1024, height=1024, encoding='PNG')
    print('Made a thumbnail of type %s taking %d bytes' % (
        mimeType, len(thumbnail)))
 
    open(outname, 'wb').write(thumbnail)

    print('thumbnail generation complete')
    # return the name of the output file
    return outname

