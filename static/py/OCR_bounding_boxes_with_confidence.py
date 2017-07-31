from PIL import Image, ImageDraw, ImageFont
from tesserocr import PyTessBaseAPI, PSM, RIL
from google_translate import *
import spacy
from generate_examples import *
import os
from CAIS import *
import random
import glob
import numpy as np
from merge_images import *
from opacityConversion import *
from randomizeStrip import *
from lineDetection import *



#Find the bounding boxes

def findBoundingBoxesWord(fname):
    """ Use OCR to find the bounding boxes of each word in a document"""
    # This opens the converted pdf as an image file
    image = Image.open(fname)
    #This converts the original image to RGBA to allow for alpha channel
    #composits (This allows for transparency in PIL)
    img = image.convert("RGBA")
    #This creates a new transparent image to composite with teh original
    tmp = Image.new('RGBA', img.size, (0,0,0,0))
    #This creates the drawing object for the overlay
    draw = ImageDraw.Draw(tmp)

    with PyTessBaseAPI() as api:
        api.SetImage(image)

        # Interate over lines using OCR
        #boxes = api.GetComponentImages(RIL.TEXTLINE, True)

        # Iterate over words using OCR
        boxes = api.GetComponentImages(RIL.WORD, True)
        #print 'Found {} textline image components.'.format(len(boxes))
        for i, (im, box, _, _) in enumerate(boxes):
            # im is a PIL image object
            # box is a dict with x, y, w and h keys
            api.SetRectangle(box['x'], box['y'], box['w'], box['h'])
            ocrResult = api.GetUTF8Text()

            #This calls the google translate function to translate a line of text for inclusion
            #transText = g_translate(ocrResult)
            #print transText

            #This gets the OCR confidence
            conf = api.MeanTextConf()

            #scale the confidence to the opacity
            opacity = opacityConversion(conf)

            #draw = ImageDraw.Draw(image)
            draw.rectangle(((box['x'],box['y']),((box['x']+box['w']),(box['y']+box['h']))), fill=(244, 167, 66,opacity))

    # This creates a composit image with the original image and the transparent overlay
    img = Image.alpha_composite(img, tmp)
    # This saves the new image
    img.save(fname)

            #print (u"Box[{0}]: x={x}, y={y}, w={w}, h={h}, "
                   #"confidence: {1}, text: {2}").format(i, conf, ocrResult, **box)


def findBoundingBoxesLine(fname, translate):
    """ Use OCR to find bounding boxes of each line in document"""
    img_processing = []
    img_patches = []
    lineLst = lineDetection(fname) #This gets threshold info for randomization
    image = Image.open(fname)
    img = image.convert("RGBA")
    imgWidth, imgHeight = img.size
    tmp = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(tmp)
    nlp = spacy.load('en')
    lowestXValue = 9999
    # set an empty variable to find the longest width of a bounding box for texture synthesis
    longestWidthValue = 0
    longestHeightValue = 0
    boundingBoxes = [] # this keep tracks of all the bounding boxes to build the new spaces

    with PyTessBaseAPI() as api:
        api.SetImage(image)
        # Interate over lines using OCR
        boxes = api.GetComponentImages(RIL.TEXTLINE, True)
        if translate == True:
            translatedBoxes = []
        
        for i, (im, box, _, _) in enumerate(boxes):
            # im is a PIL image object
            # box is a dict with x, y, w and h keys
            api.SetRectangle(box['x'], box['y'], box['w'], box['h'])

            #this caluclates the lowest x-value which indicates the margin.
            if box['x'] < lowestXValue:
                lowestXValue = box['x']

            #this tracks the longest witdth for texture synthesis
            if box['w'] > longestWidthValue:
                longestWidthValue = box['w']

            #this tracks the longest height for texture synthesis
            if box['h'] > longestHeightValue:
                longestHeightValue = box['h']

            #this tracks all the places that the texture needs to be laid
            boundingBoxes.append(box)

            ocrResult = api.GetUTF8Text()

            #Get Locations from Text for Maps WORKING
            #doc = nlp(ocrResult)

            if translate == True:
                #This calls the google translate function to translate a line of text for inclusion WORKING
                transText = g_translate(ocrResult)
                translatedBoxes.append(transText)

            #This is the OCR confidence overlays for each line...the drawing step is missing here
            #conf = api.MeanTextConf()

            #scale the confidence to the opacity
            #opacity = opacityConversion(conf)

            #draw = ImageDraw.Draw(image)
            #draw.rectangle(((box['x'],box['y']),((box['x']+box['w']),(box['y']+box['h']))), fill=(244, 167, 66,opacity))

    textureX = lowestXValue // 2

    for idx, box in enumerate(boundingBoxes):
        # Cut textures for expansion in paper backgrounds. 
        # The idea is to take a strip and randomize the pixels in blocks of some
        # number width hopefully making it possible to grow the image

        #find the centre between the 2 lines : this doesn't account for the footer FIX THIS
        if idx <= len(boundingBoxes)-2:

            box1 = boundingBoxes[idx]
            box2 = boundingBoxes[idx+1]

            # This calculatesthe middle of the space between two lines
            middleYDistance = (box2['y'] - (box1['y']+box1['h']))-1
            middleDistanceDivisor = 2
            finalMiddleDistance = middleYDistance / middleDistanceDivisor

        # This cuts a number of lines from below the text bounding box.
        textureCrop = img.crop((0, box['y']+box['h']+1, imgWidth, box['y']+box['h']+5))
        
        img_block = randomizeStrip(textureCrop, lineLst)
        compImage = merge_image_list(img_block)
        img_patches.append(compImage)
        # compImage.save(open('./image_processing/img_{:03d}.png'.format(idx), 'w'))

    # This creates a composite image with the original image and the transparent overlay
    img = Image.alpha_composite(img, tmp)
    width, height = img.size

    imageRebuildCounter = 0
    # iterate through the bounding boxes and crop them out accounting for the first and the last chop
    # to keep headers and footers
    for i, box in enumerate(boundingBoxes):
        if i == 0:
            tmpImageCrop = img.crop((0, 0, width, box['y']+box['h']))
        elif i == len(boundingBoxes):
            tmpImageCrop = img.crop((0, box['y'], width, height))
        else:
            tmpImageCrop = img.crop((0, box['y'], width, box['y']+box['h']))
        img_processing.append(tmpImageCrop)

    spreadCounter = 20
    compImage = None
    # merge everything back together to a composite image
    for i in range(0, len(img_processing)):
        if i == 0:
            compImage = merge_images(img_processing[i], img_patches[i], "vertical")

            if spreadCounter > 1:
                oldCompImage = img_processing[i]
                widthOld,heightOld = oldCompImage.size

                for x in range(1,spreadCounter):
                    img_block = randomizeStrip(img_patches[i],lineLst)
                    stripImage = merge_image_list(img_block)
                    compImage = merge_images(compImage, stripImage, "vertical")

                widthNew,heightNew = compImage.size
                spreadDifference = heightNew - heightOld

        elif i == len(img_processing):
            widthOld,heightOld = oldCompImage.size
            compImage = merge_images(compImage,img_processing[i],"vertical")
            widthNew,heightNew = compImage.size
            spreadDifference = heightNew - heightOld

        else:
            compImage = merge_images(compImage,img_processing[i],"vertical")
            widthOld,heightOld = oldCompImage.size
            compImage = merge_images(compImage,img_patches[i],"vertical")

            if spreadCounter > 1:
                for x in range(1,spreadCounter):
                    img_block = randomizeStrip(img_patches[i], lineLst)
                    stripImage = merge_image_list(img_block)
                    compImage = merge_images(compImage,stripImage,"vertical")

                widthNew,heightNew = compImage.size
                spreadDifference = heightNew - heightOld

        # if we are translating, insert the translation
        if translate == True:
            draw = ImageDraw.Draw(compImage)
            font = ImageFont.truetype("./templates/ARIALUNI.TTF", 40)
            draw.text((boundingBoxes[i]['x'], heightOld+(spreadDifference/3)),translatedBoxes[i],(0,0,0),font=font)

    compImage.save(open('./image_processing/compImage.jpg', 'w'))