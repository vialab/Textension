from PIL import Image, ImageDraw
import random
import os
from merge_images import *

def randomizeStrip(im, lineLst):
    """ Randomize the pixels within a background block """
    pixelCutWidth = 5
    rgb_im = im.convert('RGB')
    imWidth, imHeight = im.size

    noise = True
    img_patches = []
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
        im2 = Image.new('RGB', (pixelCutWidth, imHeight))

        if noise:
            random.shuffle(pixelList)
            
        im2.putdata(pixelList)
        img_patches.append(im2)

    #stitch the temp files together put in outputs
    compImage = None
    for i in range(0,len(img_patches)):
        #this might have a problem with dropping a pixel if the width of the image is an odd number
        if len(img_patches) > 1:
            # we got patches
            if i == 0:
                compImage = merge_images(img_patches[0],img_patches[1],"horizontal")
            elif i > 1:
                compImage = merge_images(compImage, img_patches[i],"horizontal")
        else:
            # nothing to merge
            compImage = img_patches[0]

    return compImage
