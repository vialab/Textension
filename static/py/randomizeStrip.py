from PIL import Image, ImageDraw
import random
import os
from merge_images import *

def randomizeStrip(im, lineLst):

    im = Image.open(im)
    

    pixelCutWidth = 5
    rgb_im = im.convert('RGB')
    imWidth, imHeight = im.size

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

        im2 = Image.new('RGB', (pixelCutWidth, imHeight))


        if noise == False:

            im2.putdata(pixelList)
            im2.save("/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/img_{:03d}.jpg".format(randomImageCounter))
            noise = True
        else:

            random.shuffle(pixelList)
            im2.putdata(pixelList)
            im2.save("/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/img_{:03d}.jpg".format(randomImageCounter))



        randomImageCounter = randomImageCounter + 1

    #stitch the temp files together put in outputs

    lst = os.listdir('/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp')
    lst.sort()
    if ".DS_Store" in lst:
        lst.remove(".DS_Store")
    firstPass = True
    for i in range(1,len(lst)):
        #this might have a problem with dropping a pixel if the width of the image is an odd number

        if firstPass:

            compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+lst[0],'/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+lst[1],"horizontal")
            compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/img_patches/compImage.jpg', 'w'))
            firstPass = False

        else:
            compImage = merge_images('/Users/adambradley/Python_Dev/InLineViz/img_patches/compImage.jpg','/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+ lst[i],"horizontal")
            compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/img_patches/compImage.jpg', 'w'))


    return '/Users/adambradley/Python_Dev/InLineViz/img_patches/compImage.jpg'
    #delete the files in the tmp folder

    for x in lst:
        os.remove('/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/'+x)
