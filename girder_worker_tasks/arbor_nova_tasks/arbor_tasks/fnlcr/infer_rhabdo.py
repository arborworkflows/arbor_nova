from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile


# included for the source python algorithm
import os

#import torch
import cv2

import numpy as np
import pathlib

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
def preprocess(img):
    cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    target_dimensions = (480,384)
    resized = cv2.resize(img,target_dimensions,interpolation=cv2.INTER_AREA)
    # convert to tensor and normalize pixel values to match training
    img_as_tensor = resized.transpose(2,0,1).astype('float32')/256.0
    return img_as_tensor 


#-------------------------------------------

girder_job(title='infer_rhabdo')
@app.task(bind=True)
def infer_rhabdo(self,image_file,**kwargs):

    print(" input tif image filename = {}".format(image_file))

    #
    # Check that the datafiles exist
    #
    if(file_exists(image_file,'tif image') is  True): 
        print('found image file')
    else:
        print('could not read image file')
        quit()

    # setup the GPU environment for pytorch
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    DEVICE = 'cuda'

    # setup the location where a previously trained model is available
    path = '/home/vagrant/arbor_nova/girder_worker_tasks/arbor_nova_tasks/arbor_tasks/fnlcr/'

    # load the model structure and restore the weights in the pretrained layers
    print('loading DL network definition')
    print('temporily disabled for testing')
    #loaded_model = torch.load(path+'car_seg_model.pth')
    #loaded_model.eval()

    print('load input tensor')
    img_infer = cv2.imread(image_file)
    img_tensor = preprocess(img_infer)
    print('perform forward inferencing')
    print('temporarily disabled for testing.  Passing input image as output.')
    #input_tensor = torch.from_numpy(img_tensor).to(DEVICE).unsqueeze(0)
    #predict_image = loaded_model.predict(input_tensor)
    print('inferencing completed')

    #scale the output image so the segmentation results are visible
    # NOTE: TIF can handle float pixels. do we need to convert to utin8 here ?

    #predict_image = (predict_image*256.0).astype('uint8')
    predict_image = img_infer

    # generate unique names for multiple runs.  Add extension so it is easier to use
    outname = NamedTemporaryFile(delete=False).name+'.png'

    # write the output object using openCV  
    print('writing output')
    cv2.imwrite(outname,predict_image) 
    print('writing completed') 

    # return the name of the output file
    return outname

