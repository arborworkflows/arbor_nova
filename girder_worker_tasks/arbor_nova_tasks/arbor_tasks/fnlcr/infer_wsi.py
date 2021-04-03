# added for girder interaction as plugin arbor task
from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

# declared for subprocess to do GPU stuff.  Package 'billiard' comes with celery
# and is a workaround for subprocess limitations on 'daemonic' processes.

import billiard as multiprocessing
from billiard import Queue, Process
import json


#-------------------------------------------

@girder_job(title='inferWSI')
@app.task(bind=True)
def infer_wsi(self,image_file,**kwargs):

    #print(" input image filename = {}".format(image_file))

    # setup the GPU environment for pytorch
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    DEVICE = 'cuda'

    print('perform forward inferencing')


    subprocess = False
    if (subprocess):
        # declare a subprocess that does the GPU allocation to keep the GPU memory from leaking
        msg_queue = Queue()
        gpu_process = Process(target=start_inference, args=(msg_queue,image_file))
        gpu_process.start()
        predict_image = msg_queue.get()
        gpu_process.join()     
    else:
        predict_image = start_inference_mainthread(image_file)
  
    predict_bgr = cv2.cvtColor(predict_image,cv2.COLOR_RGB2BGR)
    print('output conversion and inferencing complete')

    # generate unique names for multiple runs.  Add extension so it is easier to use
    outname = NamedTemporaryFile(delete=False).name+'.png'

    # write the output object using openCV  
    print('writing output')
    cv2.imwrite(outname,predict_bgr)
    print('writing completed')

    # new output of segmentation statistics in a string
    statistics = generateStatsString(predict_image)
    # generate unique names for multiple runs.  Add extension so it is easier to use

    statoutname = NamedTemporaryFile(delete=False).name+'.json'
    open(statoutname,"w").write(statistics)

    # return the name of the output file and the stats
    return outname,statoutname



import random
#import argparse
import torch
import torch.nn as nn
import cv2

import os, glob
import numpy as np
from skimage.io import imread, imsave
from skimage import filters
from skimage.color import rgb2gray
import gc

# from github.com/girder/large_image
import large_image

from PIL import Image, ImageColor
Image.MAX_IMAGE_PIXELS = None

import albumentations as albu
import segmentation_models_pytorch as smp

ml = nn.Softmax(dim=1)


NE = 50
ST = 100
ER = 150
AR = 200
PRINT_FREQ = 20
BATCH_SIZE = 80

ENCODER = 'efficientnet-b4'
ENCODER_WEIGHTS = 'imagenet'
ACTIVATION = None
DEVICE = 'cuda'

# the weights file is in the same directory, so make this path reflect that.  If this is 
# running in a docker container, then we should assume the weights are at the toplevel 
# directory instead

if (os.getenv('DOCKER') == 'True') or (os.getenv('DOCKER') == 'True'):
    WEIGHT_PATH = '/'
else:
    WEIGHT_PATH = '/'

# these aren't used in the girder version, no files are directly written out 
# by the routines written by FNLCR (Hyun Jung)
WSI_PATH = '.'
PREDICTION_PATH = '.'

IMAGE_SIZE = 384
IMAGE_HEIGHT = 384
IMAGE_WIDTH = 384
CHANNELS = 3
NUM_CLASSES = 5
CLASS_VALUES = [0, 50, 100, 150, 200]

BLUE = [0, 0, 255] # ARMS: 200
RED = [255, 0, 0] # ERMS: 150
GREEN = [0, 255, 0] # STROMA: 100
YELLOW = [255, 255, 0] # NECROSIS: 50
EPSILON = 1e-6

# what magnification should this pipeline run at
ANALYSIS_MAGNIFICATION = 10
THRESHOLD_MAGNIFICATION = 2.5
ASSUMED_SOURCE_MAGNIFICATION = 20.0

rot90 = albu.Rotate(limit=(90, 90), always_apply=True)
rotn90 = albu.Rotate(limit=(-90, -90), always_apply=True)

rot180 = albu.Rotate(limit=(180, 180), always_apply=True)
rotn180 = albu.Rotate(limit=(-180, -180), always_apply=True)

rot270 = albu.Rotate(limit=(270, 270), always_apply=True)
rotn270 = albu.Rotate(limit=(-270, -270), always_apply=True)

hflip = albu.HorizontalFlip(always_apply=True)
vflip = albu.VerticalFlip(always_apply=True)
tpose = albu.Transpose(always_apply=True)

pad = albu.PadIfNeeded(p=1.0, min_height=IMAGE_SIZE, min_width=IMAGE_SIZE, border_mode=0, value=(255, 255, 255), mask_value=0)

# supporting subroutines
#-----------------------------------------------------------------------------

from numpy import asarray
def _generate_th(source, height,width):
    # extract a low-res version of the entire image for tissue-detection threshold processing
    myRegion = {'top': 0, 'left': 0, 'width': width, 'height': height}
    threshold_source_image, mimetype = source.getRegion(format=large_image.tilesource.TILE_FORMAT_NUMPY,
                                                        region=myRegion,
                                                        scale={'magnification': THRESHOLD_MAGNIFICATION})
    org_height = height
    org_width =  width

    print('OTSU image')
    print(type(threshold_source_image))
    print(threshold_source_image.shape)

    thumbnail_gray = rgb2gray(threshold_source_image)
    val = filters.threshold_otsu(thumbnail_gray)
    # create empty output for threshold
    otsu_seg = np.zeros((threshold_source_image.shape[0],threshold_source_image.shape[1]), np.uint8)
    # generate a mask=true image where the source pixels were darker than the
    # # threshold value (indicating tissue instead of bright background)
    otsu_seg[thumbnail_gray <= val] = 255
    # OTSU algo. was applied at reduced scale, so scale image back up
    aug = albu.Resize(p=1.0, height=org_height, width=org_width)
    augmented = aug(image=otsu_seg, mask=otsu_seg)
    otsu_seg = augmented['mask']
    print('rescaled threshold shape is:',otsu_seg.shape)
    #imsave('otsu.png', (otsu_seg.astype('uint8')))
    print('Otsu segmentation finished')
    return otsu_seg


def _infer_batch(model, test_patch):
    # print('Test Patch Shape: ', test_patch.shape)
    with torch.no_grad():
        logits_all = model(test_patch[:, :, :, :])
        logits = logits_all[:, 0:NUM_CLASSES, :, :]
    prob_classes_int = ml(logits)
    prob_classes_all = prob_classes_int.cpu().numpy().transpose(0, 2, 3, 1)

    return prob_classes_all

def _augment(index, image):

    if index == 0:
        image= image

    if index == 1:
        augmented = rot90(image=image)
        image = augmented['image']

    if index ==2:
        augmented = rot180(image=image)
        image= augmented['image']

    if index == 3:
        augmented = rot270(image=image)
        image = augmented['image']

    if index == 4:
        augmented = vflip(image=image)
        image = augmented['image']

    if index == 5:
        augmented = hflip(image=image)
        image = augmented['image']

    if index == 6:
        augmented = tpose(image=image)
        image = augmented['image']

    return image
    
def _unaugment(index, image):

    if index == 0:
        image= image

    if index == 1:
        augmented = rotn90(image=image)
        image = augmented['image']

    if index ==2:
        augmented = rotn180(image=image)
        image= augmented['image']

    if index == 3:
        augmented = rotn270(image=image)
        image = augmented['image']

    if index == 4:
        augmented = vflip(image=image)
        image = augmented['image']

    if index == 5:
        augmented = hflip(image=image)
        image = augmented['image']

    if index == 6:
        augmented = tpose(image=image)
        image = augmented['image']

    return image

def _gray_to_color(input_probs):

    index_map = (np.argmax(input_probs, axis=-1)*50).astype('uint8')
    height = index_map.shape[0]
    width = index_map.shape[1]

    heatmap = np.zeros((height, width, 3), np.float32)

    # Background
    heatmap[index_map == 0, 0] = input_probs[:, :, 0][index_map == 0]
    heatmap[index_map == 0, 1] = input_probs[:, :, 0][index_map == 0]
    heatmap[index_map == 0, 2] = input_probs[:, :, 0][index_map == 0]

    # Necrosis
    heatmap[index_map==50, 0] = input_probs[:, :, 1][index_map==50]
    heatmap[index_map==50, 1] = input_probs[:, :, 1][index_map==50]
    heatmap[index_map==50, 2] = 0.

    # Stroma
    heatmap[index_map==100, 0] = 0.
    heatmap[index_map==100, 1] = input_probs[:, :, 2][index_map==100]
    heatmap[index_map==100, 2] = 0.

    # ERMS
    heatmap[index_map==150, 0] = input_probs[:, :, 3][index_map==150]
    heatmap[index_map==150, 1] = 0.
    heatmap[index_map==150, 2] = 0.

    # ARMS
    heatmap[index_map==200, 0] = 0.
    heatmap[index_map==200, 1] = 0.
    heatmap[index_map==200, 2] = input_probs[:, :, 4][index_map==200]

    heatmap[np.average(heatmap, axis=-1)==0, :] = 1.

    return heatmap


# return a string identifier of the basename of the current image file
def returnIdentifierFromImagePath(impath):
    # get the full name of the image
    file = os.path.basename(impath)
    # strip off the extension
    base = file.split('.')[0]
    return(base)

def displayTileMetadata(tile,region,i,j):
    if (tile.shape[0] != 384 or tile.shape[1] != 384):
        print('i,j:',i,j)
        print('tile sizeX:',tile.shape[0],'sizeY:',tile.shape[1])
        print('top:',region['top'],'left:',region['left'],'width:',region['width'],'height:',region['height'])


def isNotANumber(variable):
    # this try clause will work for integers and float values, since floats can be cast.  If the
    # variable is any other type (include None), the clause will cause an exception and we will return False
    try:
        tmp = int(variable)
        return False
    except:
        return True


#---------------- main inferencing routine ------------------
def _inference(model, image_path, BATCH_SIZE, num_classes, kernel, num_tta=1):
    model.eval()

    # open an access handler on the large image
    source = large_image.getTileSource(image_path)

    # print image metadata
    metadata = source.getMetadata()
    print(metadata)
    print('sizeX:', metadata['sizeX'], 'sizeY:', metadata['sizeY'], 'levels:', metadata['levels'])

    # figure out the size of the actual image and the size that this analysis
    # processing will run at.  The size calculations are made in two steps to make sure the
    # rescaled threshold image size and the analysis image size match without rounding error

    height_org = metadata['sizeY']
    width_org = metadata['sizeX']

    # if we are processing using a reconstructed TIF from VIPS, there will not be a magnification value.
    # So we will assume 20x as the native magnification, which matches the source data the
    # IVG  has provided.

    if isNotANumber(metadata['magnification']):
        print('warning: No magnfication value in source image. Assuming the source image is at ',
            ASSUMED_SOURCE_MAGNIFICATION,' magnification')
        metadata['magnification'] = ASSUMED_SOURCE_MAGNIFICATION
        assumedMagnification = True
    else:
        assumedMagnification = False

    # the theoretical adjustment for the magnification would be as below:
    # height_proc = int(height_org * (ANALYSIS_MAGNIFICATION/metadata['magnification']))
    # width_proc = int(width_org * (ANALYSIS_MAGNIFICATION/metadata['magnification']))

    height_proc = int(height_org * THRESHOLD_MAGNIFICATION/metadata['magnification'])*int(ANALYSIS_MAGNIFICATION/THRESHOLD_MAGNIFICATION)
    width_proc = int(width_org * THRESHOLD_MAGNIFICATION/metadata['magnification'])*int(ANALYSIS_MAGNIFICATION/THRESHOLD_MAGNIFICATION)
    print('analysis image size :',height_proc, width_proc)

    basename_string = os.path.splitext(os.path.basename(image_path))[0]
    print('Basename String: ', basename_string)

    # generate a binary mask for the image
    height_otsu = int(height_proc * THRESHOLD_MAGNIFICATION/ANALYSIS_MAGNIFICATION)
    width_otsu = int(width_proc * THRESHOLD_MAGNIFICATION / ANALYSIS_MAGNIFICATION)
    print('size of threshold mask:',height_otsu,width_otsu)
    myRegion = {'top': 0, 'left': 0, 'width': width_org, 'height': height_org}

    if assumedMagnification:
        # we have to manage the downsizing to the threshold magnification.
        threshold_source_image, mimetype = source.getRegion(format=large_image.tilesource.TILE_FORMAT_NUMPY,
                                                            region=myRegion,output={'maxWidth':width_otsu,'maxHeight':height_otsu})
        print('used maxOutput for threshold size')
    else:
        threshold_source_image, mimetype = source.getRegion(format=large_image.tilesource.TILE_FORMAT_NUMPY,
                                                        region=myRegion,
                                                        scale={'magnification': THRESHOLD_MAGNIFICATION})

    print('OTSU image')
    print(type(threshold_source_image))
    print(threshold_source_image.shape)

    thumbnail_gray = rgb2gray(threshold_source_image)
    val = filters.threshold_otsu(thumbnail_gray)
    # create empty output for threshold
    otsu_seg = np.zeros((threshold_source_image.shape[0], threshold_source_image.shape[1]), np.uint8)
    # generate a mask=true image where the source pixels were darker than the
    # # threshold value (indicating tissue instead of bright background)
    otsu_seg[thumbnail_gray <= val] = 255
    # OTSU algo. was applied at reduced scale, so scale image back up
    aug = albu.Resize(p=1.0, height=height_proc, width=width_proc)
    augmented = aug(image=otsu_seg, mask=otsu_seg)
    otsu_org = augmented['mask'] // 255
    print('rescaled threshold shape is:', otsu_org.shape)
    #imsave('otsu.png', (augmented['mask'] .astype('uint8')))
    print('Otsu segmentation finished')

    #otsu_org = _generate_th(source,height_org,width_org) // 255


    # initialize the output probability map
    prob_map_seg_stack = np.zeros((height_proc, width_proc, num_classes), dtype=np.float32)

    for b in range(num_tta):

        height = height_proc
        width = width_proc

        PATCH_OFFSET = IMAGE_SIZE // 2
        SLIDE_OFFSET = IMAGE_SIZE // 2

        # these are the counts in the x and y direction.  i.e. how many samples across the image.
        # the divident is slide_offset because this is how much the window is moved each time
        heights = (height + PATCH_OFFSET * 2 - IMAGE_SIZE) // SLIDE_OFFSET +1
        widths = (width + PATCH_OFFSET * 2 - IMAGE_SIZE) // SLIDE_OFFSET +1
        print('heights,widths:',heights,widths)

        heights_v2 = (height + PATCH_OFFSET * 2) // (SLIDE_OFFSET)
        widths_v2 = (width + PATCH_OFFSET * 2) // (SLIDE_OFFSET)
        print('heights_v2,widths_v2',heights_v2,widths_v2)

        # extend the size to allow for the whole actual image to be processed without actual
        # pixels being at a tile boundary.

        height_ext = SLIDE_OFFSET * heights + PATCH_OFFSET * 2
        width_ext = SLIDE_OFFSET * widths + PATCH_OFFSET * 2
        print('height_ext,width_ext:',height_ext,width_ext)

        org_slide_ext = np.ones((height_ext, width_ext, 3), np.uint8) * 255
        otsu_ext = np.zeros((height_ext, width_ext), np.uint8)
        prob_map_seg = np.zeros((height_ext, width_ext, num_classes), dtype=np.float32)
        weight_sum = np.zeros((height_ext, width_ext, num_classes), dtype=np.float32)

        #org_slide_ext[PATCH_OFFSET: PATCH_OFFSET + height, PATCH_OFFSET:PATCH_OFFSET + width, 0:3] = image_working[:, :,
        #                                                                                             0:3]

        # load the otsu results
        otsu_ext[PATCH_OFFSET: PATCH_OFFSET + height, PATCH_OFFSET:PATCH_OFFSET + width] = otsu_org[:, :]

        linedup_predictions = np.zeros((heights * widths, IMAGE_SIZE, IMAGE_SIZE, num_classes), dtype=np.float32)
        linedup_predictions[:, :, :, 0] = 1.0
        test_patch_tensor = torch.zeros([BATCH_SIZE, 3, IMAGE_SIZE, IMAGE_SIZE], dtype=torch.float).cuda(
            non_blocking=True)

        # get an identifier for the patch files to be written out as debugging
        unique_identifier = returnIdentifierFromImagePath(image_path)

        patch_iter = 0
        inference_index = []
        position = 0
        stopcounter = 0
        for i in range(heights-2):
            for j in range(widths-2):
                #test_patch = org_slide_ext[i * SLIDE_OFFSET: i * SLIDE_OFFSET + IMAGE_SIZE,
                #             j * SLIDE_OFFSET: j * SLIDE_OFFSET + IMAGE_SIZE, 0:3]

                # specify the region to extract and pull it at the proper magnification.  If a region is outside
                # of the image boundary, the returned tile will be padded with white pixels (background).  The region
                # coordinates are in the coordinate frame of the original, full-resolution image, so we need to calculate
                # them from the analytical coordinates
                top_in_orig = int(i * SLIDE_OFFSET * metadata['magnification']/ANALYSIS_MAGNIFICATION)
                left_in_orig = int(j * SLIDE_OFFSET * metadata['magnification'] / ANALYSIS_MAGNIFICATION)
                image_size_in_orig = int(IMAGE_SIZE* metadata['magnification'] / ANALYSIS_MAGNIFICATION)
                myRegion = {'top': top_in_orig, 'left': left_in_orig, 'width': image_size_in_orig, 'height': image_size_in_orig}
                rawtile, mimetype = source.getRegion(format=large_image.tilesource.TILE_FORMAT_NUMPY,
                                                       region=myRegion, scale={'magnification': ANALYSIS_MAGNIFICATION},
                                                        fill="white",output={'maxWidth':IMAGE_SIZE,'maxHeight':IMAGE_SIZE})
                test_patch = rawtile[:,:,0:3]
                #displayTileMetadata(test_patch,myRegion,i,j)
     
                otsu_patch = otsu_ext[i * SLIDE_OFFSET: i * SLIDE_OFFSET + IMAGE_SIZE,
                             j * SLIDE_OFFSET: j * SLIDE_OFFSET + IMAGE_SIZE]
                if np.sum(otsu_patch) > int(0.05 * IMAGE_SIZE * IMAGE_SIZE):
                    inference_index.append(patch_iter)
                    test_patch_tensor[position, :, :, :] = torch.from_numpy(test_patch.transpose(2, 0, 1)
                                                                            .astype('float32') / 255.0)
                    position += 1
                patch_iter += 1

                if position == BATCH_SIZE:
                    batch_predictions = _infer_batch(model, test_patch_tensor)
                    for k in range(BATCH_SIZE):
                        linedup_predictions[inference_index[k], :, :, :] = batch_predictions[k, :, :, :]

                    position = 0
                    inference_index = []

                # save data to look at
                #if (temp_i>100) and (temp_i<400):
                if (False):
                    np.save('hyun-patch-'+unique_identifier+'-'+str(temp_i)+'_'+str(temp_j)+'.npy', test_patch)
                    print('test_patch shape:', test_patch.shape, 'i:',temp_i,' j:',temp_j)
                    np.save('hyun-tensor-' + unique_identifier + '-' + str(temp_i) + '_' + str(temp_j) + '.npy', test_patch_tensor.cpu())
                    print('test_tensor shape:', test_patch.shape, 'i:', temp_i, ' j:', temp_j)
                    from PIL import Image
                    im = Image.fromarray(test_patch)
                    im.save('hyun-patch-'+str(temp_i)+'_'+str(temp_j)+'.jpeg')

        # Very last part of the region.  This is if there is a partial batch of tiles left at the
        # end of the image.
        batch_predictions = _infer_batch(model, test_patch_tensor)
        for k in range(position):
            linedup_predictions[inference_index[k], :, :, :] = batch_predictions[k, :, :, :]

        print('GPU inferencing complete. Constructing out image from patches')


        patch_iter = 0
        for i in range(heights - 2):
            for j in range(widths-2):
                prob_map_seg[i * SLIDE_OFFSET: i * SLIDE_OFFSET + IMAGE_SIZE,
                j * SLIDE_OFFSET: j * SLIDE_OFFSET + IMAGE_SIZE,:] \
                    += np.multiply(linedup_predictions[patch_iter, :, :, :], kernel)
                weight_sum[i * SLIDE_OFFSET: i * SLIDE_OFFSET + IMAGE_SIZE,
                j * SLIDE_OFFSET: j * SLIDE_OFFSET + IMAGE_SIZE,:] \
                    += kernel
                patch_iter += 1
        #np.save("prob_map_seg.npy",prob_map_seg)
        #np.save('weight_sum.npy',weight_sum)
        prob_map_seg = np.true_divide(prob_map_seg, weight_sum)
        prob_map_valid = prob_map_seg[PATCH_OFFSET:PATCH_OFFSET + height, PATCH_OFFSET:PATCH_OFFSET + width, :]
        prob_map_valid = _unaugment(b, prob_map_valid)
        prob_map_seg_stack += prob_map_valid / num_tta

    pred_map_final = np.argmax(prob_map_seg_stack, axis=-1)
    #np.save('prob_map_seg_stack.npy', prob_map_seg_stack)
    pred_map_final_gray = pred_map_final.astype('uint8') * 50
    pred_map_final_ones = [(pred_map_final_gray == v) for v in CLASS_VALUES]
    pred_map_final_stack = np.stack(pred_map_final_ones, axis=-1).astype('uint8')
    #np.save('pred_map_final_stack.npy', pred_map_final_stack)
    #prob_colormap = _gray_to_color(prob_map_seg_stack)
    #np.save('prob_colormap.npy', prob_colormap)
    #imsave(basename_string + '_prob.png', (prob_colormap * 255.0).astype('uint8'))

    pred_colormap = _gray_to_color(pred_map_final_stack)

    # for girder task, don't return this image, so commented out
    #imsave(basename_string + '_pred.tif', (pred_colormap * 255.0).astype('uint8'))

    # return image instead of saving directly
    return (pred_colormap*255.0).astype('uint8')


def _gaussian_2d(num_classes, sigma, mu):
    x, y = np.meshgrid(np.linspace(-1, 1, IMAGE_SIZE), np.linspace(-1, 1, IMAGE_SIZE))
    d = np.sqrt(x * x + y * y)
    # sigma, mu = 1.0, 0.0
    k = np.exp(-((d - mu) ** 2 / (2.0 * sigma ** 2)))

    k_min = np.amin(k)
    k_max = np.amax(k)

    k_normalized = (k - k_min) / (k_max - k_min)
    k_normalized[k_normalized<=EPSILON] = EPSILON

    kernels = [(k_normalized) for i in range(num_classes)]
    kernel = np.stack(kernels, axis=-1)

    print('Kernel shape: ', kernel.shape)
    print('Kernel Min value: ', np.amin(kernel))
    print('Kernel Max value: ', np.amax(kernel))

    return kernel


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


def inference_image(model, image_path, BATCH_SIZE, num_classes):
    kernel = _gaussian_2d(num_classes, 0.5, 0.0)
    predict_image = _inference(model, image_path, BATCH_SIZE, num_classes, kernel, 1)
    return predict_image

# this has been extended into a subprocess by adding the message queue argument and 
# calling it via a Python multiprocessing.Process()

def start_inference(msg_queue, image_file):
    reset_seed(1)

    best_prec1_valid = 0.
    #torch.backends.cudnn.benchmark = True

    #saved_weights_list = sorted(glob.glob(WEIGHT_PATH + '*.tar'))
    saved_weights_list = [WEIGHT_PATH+'model_iou_0.4996_0.5897_epoch_45.pth.tar'] 
    print(saved_weights_list)

    # create segmentation model with pretrained encoder
    model = smp.Unet(
        encoder_name=ENCODER,
        encoder_weights=ENCODER_WEIGHTS,
        classes=len(CLASS_VALUES),
        activation=ACTIVATION,
        aux_params=None,
    )

    model = nn.DataParallel(model)
    model = model.cuda()
    print('load pretrained weights')
    model = load_best_model(model, saved_weights_list[-1], best_prec1_valid)
    print('Loading model is finished!!!!!!!')

    # return image data so girder toplevel task can write it out
    predict_image = inference_image(model,image_file, BATCH_SIZE, len(CLASS_VALUES))

    # put the filename of the image in the message queue and return it to the main process
    msg_queue.put(predict_image)
    # not needed anymore, returning value through message queue
    #return predict_image

def start_inference_mainthread(image_file):
    reset_seed(1)

    best_prec1_valid = 0.
    #torch.backends.cudnn.benchmark = True

    #saved_weights_list = sorted(glob.glob(WEIGHT_PATH + '*.tar'))
    saved_weights_list = [WEIGHT_PATH+'model_iou_0.4996_0.5897_epoch_45.pth.tar'] 
    print(saved_weights_list)

    print('about to instantiate model on GPU')
    # create segmentation model with pretrained encoder
    model = smp.Unet(
        encoder_name=ENCODER,
        encoder_weights=ENCODER_WEIGHTS,
        classes=len(CLASS_VALUES),
        activation=ACTIVATION,
        aux_params=None,
    )

    print('model created')
    model = nn.DataParallel(model)
    print('data parallel done')
    model = model.cuda()
    print('moved to gpu.  now load pretrained weights')
    model = load_best_model(model, saved_weights_list[-1], best_prec1_valid)
    print('Loading model is finished!!!!!!!')

    # return image data so girder toplevel task can write it out
    predict_image = inference_image(model,image_file, BATCH_SIZE, len(CLASS_VALUES))

    # return the image to the main process
    return predict_image


# calculate the statistics for the image by converting to numpy and comparing masks against
# the tissue classes. create masks for each class and count the number of pixels

def generateStatsString(predict_image):
    # ERMS=red, ARMS=blue. Stroma=green, Necrosis = RG (yellow)
    img_arr = np.array(predict_image)
    # calculate total pixels = height*width
    total_pixels = img_arr.shape[0]*img_arr.shape[1]
    # count the pixels in the non-zero masks
    erms_count = np.count_nonzero((img_arr == [255, 0, 0]).all(axis = 2))
    stroma_count = np.count_nonzero((img_arr == [0, 255, 0]).all(axis = 2)) 
    arms_count = np.count_nonzero((img_arr == [0, 0, 255]).all(axis = 2)) 
    necrosis_count = np.count_nonzero((img_arr == [255, 255, 0]).all(axis = 2)) 
    print(f'erms {erms_count}, stroma {stroma_count}, arms {arms_count}, necrosis {necrosis_count}')
    erms_percent = erms_count / total_pixels * 100.0
    arms_percent = arms_count / total_pixels * 100.0
    necrosis_percent = necrosis_count / total_pixels * 100.0
    stroma_percent = stroma_count / total_pixels * 100.0
    # pack output values into a string returned as a file
    #statsString = 'ERMS:',erms_percent+'\n'+
    #              'ARMS:',arms_percent+'\n'+
    #              'stroma:',stroma_percent+'\n'+
    #              'necrosis:',necrosis_percent+'\n'
    statsDict = {'ERMS':erms_percent,
                 'ARMS':arms_percent, 
                 'stroma':stroma_percent, 
                 'necrosis':necrosis_percent }
    # convert dict to json string
    print('statsdict:',statsDict)
    statsString = json.dumps(statsDict)
    return statsString