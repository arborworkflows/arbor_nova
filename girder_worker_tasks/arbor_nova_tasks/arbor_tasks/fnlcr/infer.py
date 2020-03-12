from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile


# **** turn off includes temporarily until finished with this app

# included for the source python algorithm
#from tensorflow.keras.models import *
#from tensorflow.keras.preprocessing import image
#from tensorflow.keras.preprocessing.image import ImageDataGenerator, array_to_img,img_to_array, load_img
#from PIL import Image
#from infer_models import *

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


# Important Global Variables
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
model_name = "VGG-19"

# Defining Pre-Trained Models
def unfreeze_layers(model_name, conv_base):
    
    # Unfreezing all
    conv_base.trainable = True
    
    # Case for VGG-16
    if (model_name == "VGG-16" or model_name == "VGG-19"):
        set_trainable = False
        for layer in conv_base.layers:
            if layer.name == 'block5_conv1':
                set_trainable = True
            if set_trainable:
                layer.trainable = True
            else:
                layer.trainable = False
    
    # Case for Xception            
    elif (model_name == "Xception"):
        for layer in conv_base.layers[:10]:
            layer.trainable = False
    
    # Case for ResNetV2        
    elif (model_name == "ResNetV2"):
        for layer in conv_base.layers[:26]:
            layer.trainable = False
    
    # Case for InceptionV3
    elif (model_name == "InceptionV3"):
        for layer in conv_base.layers[:249]:
            layer.trainable = False
            
    # Case for InceptionResNetV2
    elif (model_name == "InceptionResNetV2"):
        set_trainable = False
        for layer in conv_base.layers:
            if layer.name == 'block8_9_mixed':
                set_trainable = True
            if set_trainable:
                layer.trainable = True
            else:
                layer.trainable = False
                
    # Case for MobileNet
    elif (model_name == "MobileNet" or model_name == "MobileNetV2"):
        for layer in conv_base.layers[:10]:
            layer.trainable = False
    
    # Case for DenseNet
    elif (model_name == "DenseNet"):
        for layer in conv_base.layers[:15]:
            layer.trainable = False
    
    # Case for NASNetLarge
    elif (model_name == "NASNetLarge"):
        set_trainable = False
        for layer in conv_base.layers:
            if layer.name == 'activation_253':
                set_trainable = True
            if set_trainable:
                layer.trainable = True
            else:
                layer.trainable = False




#-------------------------------------------

@girder_job(title='infer')
@app.task(bind=True)
def infer(self,fasta_file,**kwargs):

    print(" input image filename = {}".format(fasta_file))

    #
    # Check that the datafiles exist
    #
    if(file_exists(image_file,'numpy array') is  True): 
        print('found image array file')
    else:
        print('could not read image array file')
        quit()


    # first load the model structure, then restore the weights in the pretrained layers
    print('loading DL network definition')
    conv_base = return_pretrained(model_name)
    model = build_model(conv_base)
    unfreeze_layers("", conv_base)
    model = load_model(path + model_name + ".h5")

    test_image = image.load_img(image_file, target_size=(425, 256))

    # Casting the image into an array
    test_image = image.img_to_array(test_image)

    # E xpanding the dimensions of the image
    test_image = np.expand_dims(test_image, axis = 0)

    # Dividing by 255
    test_image = test_image / 255

    """ Uncomment once machine is freed up """

    # Predicting the type of the test image
    result = model.predict(test_image)
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

