from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile


# included for the source python algorithm
# commented out for RMS docker container     
#from keras.models import load_model
#from keras.models import model_from_json

from skimage.transform import resize
from skimage.io import imsave
import numpy as np
import json
import pathlib

# this is just included for reference on how to decorate 
# a function to be called from girder through arbor_nova plugin

#@girder_job(title='PolyA')
#@app.task(bind=True)
#def column_append(self, in_filepath, **kwargs):
#    outname = 'outfile.csv'
#    with open(outname, 'w') as tmp:
#        with open(in_filepath, 'r') as csv:
#            for line in csv:
#                outline = line.strip() + ', newcol\n'
#                tmp.write(outline)
#
#    return outname

#
# Define a function to check whether the files exist and print a message if not
#
def file_exists(f,msg):
    path=pathlib.Path(f)
    if(path.is_file() is not True):
        print("The {} file {} does not exist. Please provide a valid {} file.".format(msg,f,msg))
        return False
    else:
        return True

# resize the image array to match the size the network is trained for and convert to floating point
def preprocess(imgs):
    img_rows = 256
    img_cols = 256

    imgs_p = np.ndarray((imgs.shape[0], img_rows, img_cols), dtype=np.float32)
    for i in range(imgs.shape[0]):
        imgs_p[i] = resize(imgs[i], (img_cols, img_rows), preserve_range=True)

    imgs_p = imgs_p[..., np.newaxis]
    return imgs_p

#-------------------------------------------

@girder_job(title='infer')
@app.task(bind=True)
def infer(self,fasta_file,**kwargs):

    print(" input tensor array filename = {}".format(fasta_file))

    #
    # Check that the datafiles exist
    #
    if(file_exists(fasta_file,'numpy array') is  True): 
        print('found image array file')
    else:
        print('could not read image array file')
        quit()


    # this network uses a custom loss function, so it is easier to load in two steps using JSON
    #modelfile = 'pdx_unet_saved.h5'
    #model = load_model(path+modelfile)
    path = '/home/vagrant/arbor_nova/girder_worker_tasks/arbor_nova_tasks/arbor_tasks/fnlcr/'

    # first load the model structure, then restore the weights in the pretrained layers
    print('loading DL network definition')
    json_file = open(path+'infer_pdx_model.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    print('loading DL network weights')
    loaded_model.load_weights(path+"infer_model_weights_unet.h5")

    print('load input tensor')
    imgs_infer = np.load(fasta_file)
    imgs_infer = preprocess(imgs_infer)
    print('preform forward inferencing')
    predict_images = loaded_model.predict(imgs_infer)
    print('inferencing completed')

    #  Print the output 
    #
    # generate unique names for multiple runs?  Add extension so it is easier to use
    outname = NamedTemporaryFile(delete=False).name+'.npy'

    # write the output object using numpy  
    print('writing output')
    np.save(outname,predict_images)
    print('writing completed') 

    # return the name of the output file
    return outname

