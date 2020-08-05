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


def insertMaps(fname):

    #This gets threshold info for randomization
    #lineLst = lineDetection(fname)

    # This opens the converted pdf as an image file
    image = Image.open(fname)
    #This converts the original image to RGBA to allow for alpha channel
    #composits (This allows for transparency in PIL)
    img = image.convert("RGBA")
    #get the image height and widtch
    imgWidth, imgHeight = img.size
    #This creates a new transparent image to composite with teh original
    tmp = Image.new('RGBA', img.size, (0,0,0,0))
    #This creates the drawing object for the overlay
    draw = ImageDraw.Draw(tmp)
    #Load the spacy model for location recognition
    nlp = spacy.load('en')
    # set an empty variable to find the lowest x
    lowestXValue = 9999
    # set an empty variable to find the longest width of a bounding box for texture synthesis
    longestWidthValue = 0
    # set an empty variable to find the longest width of a bounding box for texture synthesis
    longestHeightValue = 0
    # this keep tracks of all the bounding boxes to build the new spaces
    boundingBoxes = []
    #make a list here of the lines to adjust...put just the bounding boxes into a list that have place names
    entityBoxes = {}

    with PyTessBaseAPI() as api:
        api.SetImage(image)

        # Interate over lines using OCR
        #boxes = api.GetComponentImages(RIL.TEXTLINE, True)

        # Iterate over words using OCR
        boxes = api.GetComponentImages(RIL.TEXTLINE, True)

        boxCount = 0
        #print 'Found {} textline image components.'.format(len(boxes))
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

            #This get the OCR text for the given line
            ocrResult = api.GetUTF8Text()

            #Get Locations from Text for Maps WORKING

            doc = nlp(ocrResult)

            for ent in doc.ents:

                if ent.label_ == 'NORP':
                    #print(ent.label_, ent.text)
                    #entityBoxes.append([boxCount,ent.text,ent.label_])
                    if boxCount in entityBoxes:

                        entityBoxes[boxCount].append([ent.text,ent.label_])
                    else:
                        entityBoxes[boxCount]=[[ent.text,ent.label_]]


            boxCount = boxCount + 1
        print(entityBoxes)






    # for box in boundingBoxes:
    #
    #     # This cuts a number of lines from below the text bounding box.
    #
    #     textureCrop = img.crop((0, box['y']+box['h']+1, imgWidth, box['y']+box['h']+5))
    #     textureCrop.save("/Users/adambradley/Python_Dev/InLineViz/img_patches/inputs/img_{:03d}.jpg".format(boxCounter))
    #
    #     im = Image.open("/Users/adambradley/Python_Dev/InLineViz/img_patches/inputs/img_{:03d}.jpg".format(boxCounter))
    #
    #
    #     pixelCutWidth = 5
    #     rgb_im = im.convert('RGB')
    #     imWidth, imHeight = im.size
    #
    #     noise = True
    #     randomImageCounter = 0
    #     for i in range(0,imWidth,pixelCutWidth):
    #         for t in lineLst:
    #             if abs(t-i) <= 25:
    #                 noise = False
    #
    #
    #         z = []
    #         pixelList = []
    #         for y in range(imHeight):
    #
    #             for x in range(pixelCutWidth):
    #                 r, g, b = rgb_im.getpixel((i+x, y))
    #                 pixelList.append(tuple([r,g,b]))
    #
    #         #Create a new image from random pixel choices
    #
    #         im2 = Image.new('RGB', (pixelCutWidth, imHeight))
    #
    #         if noise == False:
    #
    #             im2.putdata(pixelList)
    #             im2.save("/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/img_{:03d}.jpg".format(randomImageCounter))
    #             noise = True
    #
    #         else:
    #             random.shuffle(pixelList)
    #             im2.putdata(pixelList)
    #
    #             im2.save("/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/img_{:03d}.jpg".format(randomImageCounter))
    #
    #
    #
    #         randomImageCounter = randomImageCounter + 1
    #
    #     #stitch the temp files together put in outputs
    #
    #     lst = os.listdir('/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp')
    #     lst.sort()
    #     if ".DS_Store" in lst:
    #         lst.remove(".DS_Store")
    #     firstPass = True
    #     for i in range(1,len(lst)):
    #         #this might have a problem with dropping a pixel if the width of the image is an odd number
    #
    #         if firstPass:
    #
    #             compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+lst[0],'/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+lst[1],"horizontal")
    #             compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/img_patches/compImage.jpg', 'w'))
    #             firstPass = False
    #
    #
    #
    #         else:
    #             compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/img_patches/compImage.jpg','/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+ lst[i],"horizontal")
    #             compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/img_patches/compImage.jpg', 'w'))
    #
    #     compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/img_{:03d}.jpg'.format(boxCounter), 'w'))
    #     #delete the files in the tmp folder
    #
    #     for x in lst:
    #         os.remove('/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+x)
    #
    #
    #     boxCounter = boxCounter + 1
    #
    # # This creates a composite image with the original image and the transparent overlay
    # img = Image.alpha_composite(img, tmp)
    #
    # #rebuild the image with spaces
    # #get the height and width of the image
    # width, height = img.size
    #
    # #set a counter to rebuild the image with
    # imageRebuildCounter = 0
    #
    # #iterate through the bounding boxes and crop them out accounting for the first and the last chop
    # #to keep headers and footers
    #
    # for box in boundingBoxes:
    #     if imageRebuildCounter == 0:
    #         tmpImageCrop = img.crop((0, 0, width, box['y']+box['h']))
    #         tmpImageCrop.save("/Users/adambradley/Python_Dev/InLineViz/image_processing/img_{:03d}.jpg".format(imageRebuildCounter))
    #
    #
    #     elif imageRebuildCounter == len(boundingBoxes):
    #         tmpImageCrop = img.crop((0, box['y'], width, height))
    #         tmpImageCrop.save("/Users/adambradley/Python_Dev/InLineViz/image_processing/img_{:03d}.jpg".format(imageRebuildCounter))
    #
    #
    #     else:
    #
    #         tmpImageCrop = img.crop((0, box['y'], width, box['y']+box['h']))
    #         tmpImageCrop.save("/Users/adambradley/Python_Dev/InLineViz/image_processing/img_{:03d}.jpg".format(imageRebuildCounter))
    #
    #     imageRebuildCounter = imageRebuildCounter + 1
    #
    # #iterate through the images and the texture patches one by one to build one big image
    # #fnames1 = os.listdir('Users/adambradley/Python_Dev/InLineViz/image_processing/')
    # #fnames2 = os.listdir('Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/')
    #
    #
    # imageCounter = 0
    # spreadCounter = 20
    # totalSpreadCount = 0
    # firstPass = True
    # lst = os.listdir('/Users/adambradley/Python_Dev/InLineViz/image_processing/')
    # if ".DS_Store" in lst:
    #     lst.remove(".DS_Store")
    # lst.sort()
    # lst2 = os.listdir('/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/')
    # if ".DS_Store" in lst2:
    #     lst2.remove(".DS_Store")
    # lst2.sort()
    #
    # for i in range(len(lst)):
    #
    #     if firstPass:
    #         compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/'+lst[i],'/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/'+lst2[i],"vertical")
    #         #compImage = Image.Open('/Users/adambradley/Python_Dev/InLineViz/image_processing/'+lst[i])
    #
    #         #if compImage is not None:
    #             #firstPass = False
    #             #compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/'+lst[i],
    #             #'/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/'+ lst2[i],"vertical")
    #
    #         compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))
    #         firstPass = False
    #
    #         if spreadCounter > 1:
    #             oldCompImage = Image.open('/Users/adambradley/Python_Dev/InLineViz/image_processing/'+lst[i])
    #             widthOld,heightOld = oldCompImage.size
    #             #print heightOld
    #
    #             for x in range(1,spreadCounter):
    #                 fName = randomizeStrip('/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/'+ lst2[i],lineLst)
    #                 compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg',
    #                 fName,"vertical")
    #
    #                 compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))
    #
    #             widthNew,heightNew = compImage.size
    #             #print heightNew
    #             spreadDifference = heightNew - heightOld
    #             #print spreadDifference
    #
    #         #totalSpreadCount = totalSpreadCount + spreadDifference
    #         #print totalSpreadCount
    #
    #
    #         if translate == True:
    #
    #             draw = ImageDraw.Draw(compImage)
    #             # font = ImageFont.truetype(<font-file>, <font-size>)
    #             font = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 40)
    #             # draw.text((x, y),"Sample Text",(r,g,b))
    #
    #             draw.text((boundingBoxes[i]['x'], heightOld+(spreadDifference/3)),translatedBoxes[i],(0,0,0),font=font)
    #             compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))
    #
    #
    #
    #     elif i == len(lst):
    #
    #             oldCompImage = Image.open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg')
    #             widthOld,heightOld = oldCompImage.size
    #
    #             compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg','/Users/adambradley/Python_Dev/InLineViz/image_processing/'+ lst[i],"vertical")
    #             compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))
    #
    #             widthNew,heightNew = compImage.size
    #
    #             spreadDifference = heightNew - heightOld
    #
    #
    #
    #             if translate == True:
    #
    #                 draw = ImageDraw.Draw(compImage)
    #                 # font = ImageFont.truetype(<font-file>, <font-size>)
    #                 font = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 40)
    #                 # draw.text((x, y),"Sample Text",(r,g,b))
    #
    #                 draw.text((boundingBoxes[i]['x'], heightOld+(spreadDifference/3)),translatedBoxes[i],(0,0,0),font=font)
    #                 compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))
    #
    #     else:
    #         compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg','/Users/adambradley/Python_Dev/InLineViz/image_processing/'+ lst[i],"vertical")
    #         compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))
    #
    #         oldCompImage = Image.open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg')
    #         widthOld,heightOld = oldCompImage.size
    #
    #         compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg','/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/'+ lst2[i],"vertical")
    #         compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))
    #
    #         if spreadCounter > 1:
    #
    #
    #             for x in range(1,spreadCounter):
    #                 fName2 = randomizeStrip('/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/'+ lst2[i], lineLst)
    #                 compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg',fName2,"vertical")
    #                 compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))
    #
    #             widthNew,heightNew = compImage.size
    #
    #             spreadDifference = heightNew - heightOld
    #
    #         #totalSpreadCount = totalSpreadCount + spreadDifference
    #
    #
    #
    #     imageCounter = imageCounter + 1
    #
    #
    #
    # # This saves the new image
    # #compImage.save(fname)
    #
    #
    #         #print (u"Box[{0}]: x={x}, y={y}, w={w}, h={h}, "
    #                #"confidence: {1}, text: {2}").format(i, conf, ocrResult, **box)
