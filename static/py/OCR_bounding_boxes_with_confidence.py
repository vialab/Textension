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

    #This gets threshold info for randomization
    lineLst = lineDetection(fname)

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

    with PyTessBaseAPI() as api:
        api.SetImage(image)

        # Interate over lines using OCR
        #boxes = api.GetComponentImages(RIL.TEXTLINE, True)

        # Iterate over words using OCR
        boxes = api.GetComponentImages(RIL.TEXTLINE, True)
        if translate == True:
            translatedBoxes = []
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

            #doc = nlp(ocrResult)
            #for ent in doc.ents:
                #print(ent.label_, ent.text)

            if translate == True:
            #This calls the google translate function to translate a line of text for inclusion WORKING

                #This creates a list of translated text to draw on the image at the end
                transText = g_translate(ocrResult)
                translatedBoxes.append(transText)
                #print transText


            #This is the OCR confidence overlays for each line...the drawing step is missing here
            #conf = api.MeanTextConf()

            #scale the confidence to the opacity
            #opacity = opacityConversion(conf)

            #draw = ImageDraw.Draw(image)
            #draw.rectangle(((box['x'],box['y']),((box['x']+box['w']),(box['y']+box['h']))), fill=(244, 167, 66,opacity))

    #need to grab a swatch and place it in /Users/adambradley/Python_Dev/InLineViz/img_patches/inputs to texture synthsize'
    textureX = lowestXValue // 2

    #generate a texture for

    #note!!!!! delete the contents of inputs after this is done
    boxCounter = 0
    for box in boundingBoxes:

        #---texture synthesis-----

        #This was for the texture swatches that I use for texture synthesis

        #This takes a small swatch
        #textureCrop = img.crop((textureX, box['y'], (lowestXValue-textureX)+textureX, box['h']+box['y']))

        #This takes a bigger swatch
        #textureCrop = img.crop((0, box['y'], box['x'], box['h']+box['y']))

        #This saves the texture
        #textureCrop.save("/Users/adambradley/Python_Dev/InLineViz/img_patches/inputs/img_{:03d}.jpg".format(boxCounter))

        #boxCounter = boxCounter + 1

    #this creates the texture to fill the line texture(Height,Width,#_of_Kernals(can be a list)) it gets put in the output folder
    #findTextures = create_textures(longestHeightValue,imgWidth)

        #--- Seam Carving---
        #cut textures for seam carving
        # textureCrop = img.crop((0, box['y']+box['h'], imgWidth, box['y']+box['h']+5))
        # textureCrop.save("/Users/adambradley/Python_Dev/InLineViz/img_patches/inputs/img_{:03d}.jpg".format(boxCounter))
        #
        # inputFile = "/Users/adambradley/Python_Dev/InLineViz/img_patches/inputs/img_{:03d}.jpg".format(boxCounter)
        # #with open(inputFile, "rb") as f:
        #     #print("exists")
        # outputFile = "/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/img_{:03d}.jpg".format(boxCounter)
        #
        # #textureMap = "python CAIS.py -i " + inputFile + " -r "+ str(imgWidth) +" "+ str(box['h'])+ " -o " + outputFile + " -v"
        # #print textureMap
        # CAIS(inputFile, (imgWidth,box['h']), outputFile, False)
        # boxCounter = boxCounter + 1

        #--- My Own Algorithm for building backgrounds---#

        #cut textures for expansion in paper backgrounds. The idea is to take a strip and randomize the pixels in blocks of some
        # number width hopefully making it possible to grow the image

        #find the centre between the 2 lines : this doesn't account for the footer FIX THIS
        if boxCounter <= len(boundingBoxes)-2:

            box1 = boundingBoxes[boxCounter]
            box2 = boundingBoxes[boxCounter+1]

            # This calculatesthe middle of the space between two lines
            middleYDistance = (box2['y'] - (box1['y']+box1['h']))-1
            middleDistanceDivisor = 2
            finalMiddleDistance = middleYDistance / middleDistanceDivisor

            #print middleyDistance


        # This cuts a number of lines from below the text bounding box.

        textureCrop = img.crop((0, box['y']+box['h']+1, imgWidth, box['y']+box['h']+5))
        #textureCrop.save("/Users/adambradley/Python_Dev/InLineViz/img_patches/inputs/img_{:03d}.jpg".format(boxCounter))

        #im = Image.open("/Users/adambradley/Python_Dev/InLineViz/img_patches/inputs/img_{:03d}.jpg".format(boxCounter))


        pixelCutWidth = 5
        #rgb_im = im.convert('RGB')
        rgb_im = textureCrop.convert('RGB')
        #imWidth, imHeight = im.size
        imWidth, imHeight = textureCrop.size

        noise = True
        randomImageCounter = 0
        for i in range(0,imWidth,pixelCutWidth):
            for t in lineLst:
                if abs(t-i) <= 25:
                    noise = False


            z = []
            pixelList = []
            for y in range(imHeight):

                for x in range(pixelCutWidth):
                    r, g, b = rgb_im.getpixel((i+x, y))
                    pixelList.append(tuple([r,g,b]))

            #Create a new image from random pixel choices
#WORKS UP TILL HERE
            im2 = Image.new('RGB', (pixelCutWidth, imHeight))

            if noise == False:

                im2.putdata(pixelList)
                #im2.save("/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/img_{:03d}.jpg".format(randomImageCounter))
                noise = True

            else:
                random.shuffle(pixelList)
                im2.putdata(pixelList)

                #im2.save("/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/img_{:03d}.jpg".format(randomImageCounter))



            randomImageCounter = randomImageCounter + 1

        #stitch the temp files together put in outputs

        # lst = os.listdir('/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp')
        # lst.sort()
        # if ".DS_Store" in lst:
        #     lst.remove(".DS_Store")
        # firstPass = True
        # for i in range(1,len(lst)):
        #     #this might have a problem with dropping a pixel if the width of the image is an odd number
        #
        #     if firstPass:
        #
        #         compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+lst[0],'/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+lst[1],"horizontal")
        #         compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/img_patches/compImage.jpg', 'w'))
        #         firstPass = False
        #
        #
        #
        #     else:
        #         compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/img_patches/compImage.jpg','/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+ lst[i],"horizontal")
        #         compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/img_patches/compImage.jpg', 'w'))
        #
        # compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/img_{:03d}.jpg'.format(boxCounter), 'w'))

        im2.save(open('/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/img_{:03d}.jpg'.format(boxCounter), 'w'))

        #delete the files in the tmp folder

        #for x in lst:
            #os.remove('/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+x)


        boxCounter = boxCounter + 1

    # This creates a composite image with the original image and the transparent overlay
    img = Image.alpha_composite(img, tmp)

    #rebuild the image with spaces
    #get the height and width of the image
    width, height = img.size

    #set a counter to rebuild the image with
    imageRebuildCounter = 0

    #iterate through the bounding boxes and crop them out accounting for the first and the last chop
    #to keep headers and footers

    for box in boundingBoxes:
        if imageRebuildCounter == 0:
            tmpImageCrop = img.crop((0, 0, width, box['y']+box['h']))
            tmpImageCrop.save("/Users/adambradley/Python_Dev/InLineViz/image_processing/img_{:03d}.jpg".format(imageRebuildCounter))


        elif imageRebuildCounter == len(boundingBoxes):
            tmpImageCrop = img.crop((0, box['y'], width, height))
            tmpImageCrop.save("/Users/adambradley/Python_Dev/InLineViz/image_processing/img_{:03d}.jpg".format(imageRebuildCounter))


        else:

            tmpImageCrop = img.crop((0, box['y'], width, box['y']+box['h']))
            tmpImageCrop.save("/Users/adambradley/Python_Dev/InLineViz/image_processing/img_{:03d}.jpg".format(imageRebuildCounter))

        imageRebuildCounter = imageRebuildCounter + 1

    #iterate through the images and the texture patches one by one to build one big image
    #fnames1 = os.listdir('Users/adambradley/Python_Dev/InLineViz/image_processing/')
    #fnames2 = os.listdir('Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/')


    imageCounter = 0
    spreadCounter = 20
    totalSpreadCount = 0
    firstPass = True
    lst = os.listdir('/Users/adambradley/Python_Dev/InLineViz/image_processing/')
    if ".DS_Store" in lst:
        lst.remove(".DS_Store")
    lst.sort()
    lst2 = os.listdir('/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/')
    if ".DS_Store" in lst2:
        lst2.remove(".DS_Store")
    lst2.sort()

    for i in range(len(lst)):

        if firstPass:
            compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/'+lst[i],'/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/'+lst2[i],"vertical")
            #compImage = Image.Open('/Users/adambradley/Python_Dev/InLineViz/image_processing/'+lst[i])

            #if compImage is not None:
                #firstPass = False
                #compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/'+lst[i],
                #'/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/'+ lst2[i],"vertical")

            compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))
            firstPass = False

            if spreadCounter > 1:
                oldCompImage = Image.open('/Users/adambradley/Python_Dev/InLineViz/image_processing/'+lst[i])
                widthOld,heightOld = oldCompImage.size
                #print heightOld

                for x in range(1,spreadCounter):
                    fName = randomizeStrip('/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/'+ lst2[i],lineLst)
                    compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg',
                    fName,"vertical")

                    compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))

                widthNew,heightNew = compImage.size
                #print heightNew
                spreadDifference = heightNew - heightOld
                #print spreadDifference

            #totalSpreadCount = totalSpreadCount + spreadDifference
            #print totalSpreadCount


            if translate == True:

                draw = ImageDraw.Draw(compImage)
                # font = ImageFont.truetype(<font-file>, <font-size>)
                font = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 40)
                # draw.text((x, y),"Sample Text",(r,g,b))

                draw.text((boundingBoxes[i]['x'], heightOld+(spreadDifference/3)),translatedBoxes[i],(0,0,0),font=font)
                compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))



        elif i == len(lst):

                oldCompImage = Image.open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg')
                widthOld,heightOld = oldCompImage.size

                compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg','/Users/adambradley/Python_Dev/InLineViz/image_processing/'+ lst[i],"vertical")
                compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))

                widthNew,heightNew = compImage.size

                spreadDifference = heightNew - heightOld



                if translate == True:

                    draw = ImageDraw.Draw(compImage)
                    # font = ImageFont.truetype(<font-file>, <font-size>)
                    font = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 40)
                    # draw.text((x, y),"Sample Text",(r,g,b))

                    draw.text((boundingBoxes[i]['x'], heightOld+(spreadDifference/3)),translatedBoxes[i],(0,0,0),font=font)
                    compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))

        else:
            compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg','/Users/adambradley/Python_Dev/InLineViz/image_processing/'+ lst[i],"vertical")
            compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))

            oldCompImage = Image.open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg')
            widthOld,heightOld = oldCompImage.size

            compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg','/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/'+ lst2[i],"vertical")
            compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))

            if spreadCounter > 1:


                for x in range(1,spreadCounter):
                    fName2 = randomizeStrip('/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs/'+ lst2[i], lineLst)
                    compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg',fName2,"vertical")
                    compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))

                widthNew,heightNew = compImage.size

                spreadDifference = heightNew - heightOld

            #totalSpreadCount = totalSpreadCount + spreadDifference

            if translate == True:


                draw = ImageDraw.Draw(compImage)
                # font = ImageFont.truetype(<font-file>, <font-size>)
                font = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 40)
                # draw.text((x, y),"Sample Text",(r,g,b))

                draw.text((boundingBoxes[i]['x'], heightOld+(spreadDifference/3)),translatedBoxes[i],(0,0,0),font=font)
                compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/image_processing/compImage.jpg', 'w'))

        imageCounter = imageCounter + 1



    # This saves the new image
    #compImage.save(fname)


            #print (u"Box[{0}]: x={x}, y={y}, w={w}, h={h}, "
                   #"confidence: {1}, text: {2}").format(i, conf, ocrResult, **box)
