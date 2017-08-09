from wand.image import Image
from PIL import Image as PI
import pyocr
import pyocr.builders
import io
import os

#Note: I imported Image from PIL as PI because otherwise it would have conflicted with the Image module from wand.image.
#For those on mac and using homebrew, it seems like Wand doesn't support imagemagick 7 yet as mentioned in other answers.

#There's a new brew formula for Imagemagick 6 which can be used to install the older version in the meanwhile:
#brew install imagemagick@6
#Create a symlink to this newly installed dylib file as mentioned in other answer to get things working.
#ln -s /usr/local/Cellar/imagemagick@6/6.9.7-4/lib/libMagickWand-6.Q16.dylib /usr/local/lib/libMagickWand.dylib


#This converts a pdf to jpeg
def convertPDFToJPG(fname):
    image_pdf = Image(filename=fname, resolution=300)
    image_jpeg = image_pdf.convert('jpeg')

    #need to write the file here
    image_jpeg.save(filename=fname+".jpg")

    #delete the pdf file
    os.remove(fname)


# Digits - Only Tesseract (not 'libtesseract' yet !)
def findDigitsInImage(fname):

    digits = tool.image_to_string(
        Image.open(fname), #png image
        lang=lang,
        builder=pyocr.tesseract.DigitBuilder()
    )


#this detects orientation
def detectOrientationOfImage(imageName):
    if tool.can_detect_orientation():
        orientation = tool.detect_orientation(
            Image.open(imageName), #png Image
            lang='fra'
        )
        pprint("Orientation: {}".format(orientation))
