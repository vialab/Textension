from PIL import Image, ImageDraw
import random
import os
from merge_images import *

def randomizeStrip(im, lineLst):
    """ Return blocks of randomized pixels in a single strip """
    pixelCutWidth = 5
    rgb_im = im.convert('RGB')
    imWidth, imHeight = im.size

    noise = True
    img_block = []
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
        img_block.append(im2)

    return img_block
