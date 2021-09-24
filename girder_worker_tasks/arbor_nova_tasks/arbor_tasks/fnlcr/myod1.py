# added for girder interaction as plugin arbor task
from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

import billiard as multiprocessing
from billiard import Queue, Process 
import json
import sys

#---------

import torch
from torch.utils.data import Dataset as BaseDataset
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
import torch.nn.functional as F
from torch.autograd import Function
from torchvision import datasets, models, transforms
import torchnet.meter.confusionmeter as cm

from sklearn.preprocessing import label_binarize
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.metrics import auc as calc_auc

import openslide as op
import argparse
import numpy as np
import torchvision
import cv2
import time
from skimage.io import imread
from tifffile import imsave
import matplotlib.pyplot as plt
import time
import random
import os, glob
import copy
import pandas as pd
import albumentations as albu
from albumentations import Resize
import gc
import timm
from radam import RAdam

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

REPORTING_INTERVAL = 10

IMAGE_SIZE = 224
PRINT_FREQ = 20
class_names = ['Neg', 'Pos']
num_classes = len(class_names)

## MYOD1 heatmap will be saved in the inference_path folder
#inference_output = './For_Curtis/Inferenced/'

## MYOD1 WSIs tiff to inference location
#inference_input_tiff = './For_Curtis/20x/'

## MYOD1 WSIs svs to inference location
#inference_input_svs = './For_Curtis/svs/'


#-------------------------------------------
# girder job definition to enable execution by girder_worker

@girder_job(title='myod1')
@app.task(bind=True)
def myod1(self,image_file, segment_image_file,**kwargs):

    print(" input image filename = {}".format(image_file))

    # setup the GPU environment for pytorch
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    DEVICE = 'cuda'
    print('perform forward inferencing')
    predict_values = start_inferencing(image_file,segment_image_file)

    # new output of classification statistics in a string
    statistics = generateStatsString(predict_values)
    # generate unique names for multiple runs.  Add extension so it is easier to use
    statoutname = NamedTemporaryFile(delete=False).name+'.json'
    open(statoutname,"w").write(statistics)

    # return the name of the output file
    return statoutname


# calculate the statistics for the image by converting to numpy and comparing masks against
# the tissue classes. create masks for each class and count the number of pixels

def generateStatsString(predict_values):
    # any number of statistics can be returned in a JSON object.  Derived 
    # stats can be calculated here and included as other keys in the dict object
    statsDict = {'Positive Score': predict_values[0] }
    # convert dict to json string
    print('statsdict:',statsDict)
    statsString = json.dumps(statsDict)
    return statsString


#-------------------------------------------
# from the MYOD1 script

def reset_seed(seed):
    """
    ref: https://forums.fast.ai/t/accumulating-gradients/33219/28
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True


# this code was adapted from a command line script that used argparse functionality to 
# set command line arguments with defaults.  The following set of arguments includes the
# defaults and suggested options.  It is now initalized here and used in the algorithm 
# by referencing the "args" variable.  The upperT=0.99 (upper threshold) is important to 
# match the results reported in the submitted manuscript. 

from argparse import Namespace
def parse():
    args = Namespace(alpha=0.1, batch_size=400, cth=0.9, data='./For_Curtis/', \
        deterministic=False, epochs=90, evaluate=False, gnum=1, kfold=3, lowerT=0.75, \
        lr=0.1, milweight=0.6, momentum=0.9, numgenes=3, pretrained=False, print_freq=10, \
        prof=-1, resume='', start_epoch=0, sync_bn=False, tnum=1, upperT=0.99, \
        weight_decay=0.0001, workers=128)

    return args


def convert_to_tensor(batch):
    num_images = batch.shape[0]
    tensor = torch.zeros((num_images, 3, IMAGE_SIZE, IMAGE_SIZE), dtype=torch.uint8).cuda(non_blocking=True)

    mean = torch.tensor([0.0, 0.0, 0.0]).cuda().view(1, 3, 1, 1)
    std = torch.tensor([255.0, 255.0, 255.0]).cuda().view(1, 3, 1, 1)

    for i, img in enumerate(batch):
        nump_array = np.asarray(img, dtype=np.uint8)
        if (nump_array.ndim < 3):
            nump_array = np.expand_dims(nump_array, axis=-1)
        nump_array = np.rollaxis(nump_array, 2)

        tensor[i] = torch.from_numpy(nump_array)

    tensor = tensor.float()
    tensor = tensor.sub_(mean).div_(std)
    return tensor

def load_best_model(model, path_to_model, best_prec1=0.0):
    if os.path.isfile(path_to_model):
        print("=> loading checkpoint '{}'".format(path_to_model))
        checkpoint = torch.load(path_to_model, map_location=lambda storage, loc: storage)
        model.load_state_dict(checkpoint['state_dict'])
        print("=> loaded checkpoint '{}' (epoch {}), best_precision {}"
              .format(path_to_model, checkpoint['epoch'], best_prec1))
        return model
    else:
        print("=> no checkpoint found at '{}'".format(path_to_model))


class Classifier(nn.Module):
    def __init__(self, n_classes):
        super(Classifier, self).__init__()
        # self.effnet = timm.create_model('seresnet18', pretrained=True)
        self.effnet = timm.create_model('seresnet50', pretrained=True)
        in_features = 1000
        self.elu = nn.ELU()
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.25)
        self.alpha_dropout = nn.AlphaDropout(0.25)
        self.l0 = nn.Linear(in_features, 64, bias=True)
        self.l1 = nn.Linear(64, n_classes, bias=True)

    def forward(self, input):
        x = self.effnet(input)
        x = self.elu(x)
        x = self.alpha_dropout(x)
        x = self.l0(x)
        x = self.elu(x)  # 64
        x = self.alpha_dropout(x)
        x = self.l1(x)
        return x



def start_inferencing(image_file,segmentation_mask):
    reset_seed(1)
    args = parse()
    torch.backends.cudnn.benchmark = True

    # Three different networks ensembled for the full model.  For testing purposes,
    # we initialize just the first fold here and run inferencing once.  To ensemble, a 
    # loop would be added below to loop through all models for this algorithm in the models
    # directory (e.g. ./models/myod*)
    weight_path = './models/myod1_fold_01_model.pth.tar'

    ## Model instantiation and load model weight.
    ## Currently, my default setup is using 4 GPUs and batch size is 400
    ## Verified with 1 GPU and with the same batch_size of 400
    model = Classifier(num_classes)
    model.eval()
    model = nn.DataParallel(model)
    model = model.cuda()
    model = load_best_model(model, weight_path, 0.)
    print('Loading model is finished!!!!!!!')

    ## inference test svs image and calculate area under the curve
    prediction = test_auc_svs(model, image_file, segmentation_mask, args)
    return prediction


def test_auc_svs(model, inference_input, segment_input, args):
    model.eval()

    ml = nn.Softmax(dim=1)

    ## Set IMAGE_SIZE as 224
    IMAGE_SIZE = 224

 
    ## Read input WSIs to be inferenced
    test_ids = [inference_input]
    print(len(test_ids))

    ## Patient, labels variables
    patients = np.zeros(len(test_ids))
    other_index = 0

    ## Variables to calculate final outcome value
    correct_count = np.zeros(2)
    correct_probs = np.zeros(2)

    for i in range(len(test_ids)):
        file_path = test_ids[i]

        ## imgFile_id => WSI file path's basename
        imgFile_id = os.path.splitext(os.path.basename(file_path))[0]

        ## WSI's segmentation mask (extract patches only from cancerous regions)
        label_path = segment_input

        ## Read WSI
        wholeslide = op.OpenSlide(file_path)

        ## Level 0 optical magnification
        ## If it is 40.0, extract larger patches (IMAGE_SIZE*2) and downsize
        ## If it is 20.0, extract IMAGE_SIZE patch

        objective = float(wholeslide.properties[op.PROPERTY_NAME_OBJECTIVE_POWER])
        print(imgFile_id + ' Objective is: ', objective)
        assert objective >= 20.0, "Level 0 Objective should be greater than 20x"

        ## Extract WSI height and width
        sizes = wholeslide.level_dimensions[0]
        image_height = sizes[1]
        image_width = sizes[0]

        ## Resize WSI's segmentation mask to WSI's size
        label_org = imread(label_path)
        aug = Resize(p=1.0, height=image_height, width=image_width)
        augmented = aug(image=label_org, mask=label_org)
        label = augmented['mask']

        # decide how long this will take and prepare to give status updates in the log file
        iteration_count = 10
        report_interval = 1
        report_count = 0
        # report current state 
        percent_complete = 0

        ## If the Level 0 objective is 40.0
        if objective==40.0:
        ## Retrieve patches from WSI by batch_size but extract no more than 4000 patches
            for k in range(4000 // args.batch_size):
                image_width_start = 0
                image_width_end = image_width - IMAGE_SIZE*2 - 1

                image_height_start = 0
                image_height_end = image_height - IMAGE_SIZE*2 - 1

                x_coord = 0
                y_coord = 0

                patch_index = 0
                image_batch = np.zeros((args.batch_size, IMAGE_SIZE, IMAGE_SIZE, 3), np.uint8)

                ## Extract batch_size patches from WSI within cancerous regions
                for j in range(args.batch_size):
                    picked = False

                    while (picked == False):
                        ## Pick random locations withint segmentation masks first
                        x_coord = random.sample(range(image_width_start, image_width_end), 1)[0]
                        y_coord = random.sample(range(image_height_start, image_height_end), 1)[0]
                        label_patch = label[y_coord:y_coord + IMAGE_SIZE*2, x_coord:x_coord + IMAGE_SIZE*2]

                        ## Examine whether the random coordinates are within cancerous regions
                        ## If the coordinates are containing enough cancerous region 'picked = True' and If not 'picked=False'
                        if (np.sum(label_patch // 255) > int(IMAGE_SIZE*2 * IMAGE_SIZE*2 * 0.50)) and (
                                np.sum(label_patch == 127) == 0):
                            picked = True
                        else:
                            picked = False

                    ## Using the picked coordinates, extract corresponding WSI patch
                    ## Store patches in the image_batch so that it can be later inferenced at once
                    read_region = wholeslide.read_region((x_coord, y_coord), 0, (IMAGE_SIZE*2, IMAGE_SIZE*2))
                    large_image_patch = np.asarray(read_region)[:, :, :3]
                    image_aug = Resize(p=1.0, height=IMAGE_SIZE, width=IMAGE_SIZE)
                    image_augmented = image_aug(image=large_image_patch)
                    image_patch = image_augmented['image']
                    image_batch[patch_index, :, :, :] = image_patch
                    patch_index += 1

                with torch.no_grad():
                    ## Convert image_batch to pytorch tensor
                    image_tensor = convert_to_tensor(image_batch)

                    ## Inference the image_tensor (as a batch)
                    inst_logits = model(image_tensor)

                    ## Model's outcome are logit values for each patch
                    ## Need to conver them into probabilities of being MYOD1+
                    probs = ml(inst_logits)

                    ## Each patch produces two outcomes, MYOD1- and MYOD1+
                    ## Larger value's index will be the prediction for the patch (0, MYOD1-) (1, MYOD1+)
                    _, preds = torch.max(inst_logits, 1)
                    cbatch_size = len(image_tensor)

                    ## Examine all the patch's probability values
                    ## If predicted outcome's probability is greater than args.upperT, use them in the final calculation
                    ## Which means, if the model's outcome is not confident enough, we do not use them in our final calculation
                    for l in range(cbatch_size):
                        ## preds contains each patch's prediction (either 0 or 1)
                        ## index 0 means MYOD1- and index 1 means MYOD1+
                        index = preds[l].item()

                        ## Check the probability of the prediction
                        ## if it is greater than the threshold, it will be counted
                        ## correct_count: (2, ) shape
                        ## correct_count[0] contains total number of patches that are predicted as MYOD1- and has probability >= threshold
                        ## correct_count[1] contains total number of patches that are predicted as MYOD1+ and has probability >= threshold
                        if probs.data[l, index].item() >= args.upperT:
                            correct_count[index] += 1
                            correct_probs[index] += probs.data[l, index].item()

                # check that it is time to report progress.  If so, print it and flush I/O to make sure it comes 
                # out right after it is printed 
                report_count += 1
                if (report_count > report_interval):
                    percent_complete += REPORTING_INTERVAL
                    print(f'progress: {percent_complete}')
                    sys.stdout.flush()
                    report_count = 0

                ## When it arrives at the last iteration
                if k == ((4000 // args.batch_size) - 1):

                    ## If there are no predictions that are made with high conviction, decision is not made
                    if (np.sum(correct_count) == 0):
                        patients[other_index] = np.nan

                    ## If there are predictions that are made with high conviction, decision is made
                    ## Probability of WSI being predicted as MYOD1+ is as below
                    ## (# high conviction MYOD1+ predictions)/(# total number of high convictions)
                    else:
                        patients[other_index] = 1.0 * correct_count[1] / (correct_count[0] + correct_count[1])

                    other_index += 1
                    correct_count[:] = 0.
                    correct_probs[:] = 0.

        ## If the Level 0 objective is 40.0
        if objective == 20.0:
            ## Retrieve patches from WSI by batch_size but extract no more than 4000 patches
            for k in range(4000 // args.batch_size):
                image_width_start = 0
                image_width_end = image_width - IMAGE_SIZE - 1

                image_height_start = 0
                image_height_end = image_height - IMAGE_SIZE - 1

                x_coord = 0
                y_coord = 0

                patch_index = 0
                image_batch = np.zeros((args.batch_size, IMAGE_SIZE, IMAGE_SIZE, 3), np.uint8)

                ## Extract batch_size patches from WSI within cancerous regions
                for j in range(args.batch_size):
                    picked = False

                    while (picked == False):
                        ## Pick random locations withint segmentation masks first
                        x_coord = random.sample(range(image_width_start, image_width_end), 1)[0]
                        y_coord = random.sample(range(image_height_start, image_height_end), 1)[0]
                        label_patch = label[y_coord:y_coord + IMAGE_SIZE, x_coord:x_coord + IMAGE_SIZE]

                        ## Examine whether the random coordinates are within cancerous regions
                        ## If the coordinates are containing enough cancerous region 'picked = True' and If not 'picked=False'
                        if (np.sum(label_patch // 255) > int(IMAGE_SIZE * IMAGE_SIZE * 0.50)) and (
                                np.sum(label_patch == 127) == 0):
                            picked = True
                        else:
                            picked = False

                    ## Using the picked coordinates, extract corresponding WSI patch
                    ## Store patches in the image_batch so that it can be later inferenced at once
                    read_region = wholeslide.read_region((x_coord, y_coord), 0,
                                                         (IMAGE_SIZE, IMAGE_SIZE))
                    image_patch = np.asarray(read_region)[:, :, :3]
                    image_batch[patch_index, :, :, :] = image_patch
                    patch_index += 1

                with torch.no_grad():
                    ## Convert image_batch to pytorch tensor
                    image_tensor = convert_to_tensor(image_batch)

                    ## Inference the image_tensor (as a batch)
                    inst_logits = model(image_tensor)

                    ## Model's outcome are logit values for each patch
                    ## Need to conver them into probabilities of being MYOD1+
                    probs = ml(inst_logits)

                    ## Each patch produces two outcomes, MYOD1- and MYOD1+
                    ## Larger value's index will be the prediction for the patch (0, MYOD1-) (1, MYOD1+)
                    _, preds = torch.max(inst_logits, 1)
                    cbatch_size = len(image_tensor)

                    ## Examine all the patch's probability values
                    ## If predicted outcome's probability is greater than args.upperT, use them in the final calculation
                    ## Which means, if the model's outcome is not confident enough, we do not use them in our final calculation
                    for l in range(cbatch_size):
                        ## preds contains each patch's prediction (either 0 or 1)
                        ## index 0 means MYOD1- and index 1 means MYOD1+
                        index = preds[l].item()

                        ## Check the probability of the prediction
                        ## if it is greater than the threshold, it will be counted
                        ## correct_count: (2, ) shape
                        ## correct_count[0] contains total number of patches that are predicted as MYOD1- and has probability >= threshold
                        ## correct_count[1] contains total number of patches that are predicted as MYOD1+ and has probability >= threshold
                        if probs.data[l, index].item() >= args.upperT:
                            correct_count[index] += 1
                            correct_probs[index] += probs.data[l, index].item()

                # check that it is time to report progress.  If so, print it and flush I/O to make sure it comes 
                # out right after it is printed 
                report_count += 1
                if (report_count > report_interval):
                    percent_complete += REPORTING_INTERVAL
                    print(f'progress: {percent_complete}')
                    sys.stdout.flush()
                    report_count = 0

                ## When it arrives at the last iteration
                if k == ((4000 // args.batch_size) - 1):

                    ## If there are no predictions that are made with high conviction, decision is not made
                    if (np.sum(correct_count) == 0):
                        patients[other_index] = np.nan

                    ## If there are predictions that are made with high conviction, decision is made
                    ## Probability of WSI being predicted as MYOD1+ is as below
                    ## (# high conviction MYOD1+ predictions)/(# total number of high convictions)
                    else:
                        patients[other_index] = 1.0 * correct_count[1] / (correct_count[0] + correct_count[1])

        
                    other_index += 1
                    correct_count[:] = 0.
                    correct_probs[:] = 0.

    # force python garbage collection to free buffers
    gc.collect()
    print('MYOD1 inferencing complete')
    # return the array of processed patient results
    print('patients:',patients)
    return patients

# end of MYOD1 script code
#--------------------------------
