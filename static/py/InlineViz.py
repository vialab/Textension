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
import cv2
from opacityConversion import *

class InlineViz:
    """ Inline Viz wrapper object that performs all algorithm functions and 
    interfaces an image into workable components """
    # Class Variables
    img_comp = None
    img_file = None
    nlp = spacy.load("en")

    def __init__(self, stream, _translate=False, _max_size=(1024,1024), _pixel_cut_width=5, _noise_threshold=25, _spread=0, _line_buffer=1):
        """ Initialize a file to work with """
        self.max_size = _max_size # maximum size of image for resizing
        self.img_file = Image.open(stream) # image itselfs
        self.img_file.thumbnail(self.max_size, Image.ANTIALIAS) # resize image to maximum size
        self.img_width, self.img_height = self.img_file.convert("RGBA").size # resized width and height
        self.line_list = self.detectLines(self.img_file) # X coordinates for vertical lines
        self.translate = _translate # indicator for translating OCR'd text
        self.spread = _spread # multiplier for strip size
        self.pixel_cut_width = _pixel_cut_width # horizontal pixel cut size for randomization
        self.noise_threshold = _noise_threshold # vertical line detection threshold
        self.line_buffer = _line_buffer # space buffer cropping between bounding boxes
        self.img_patches = [] # strips between lines of text
        self.img_blocks = [] # lines of text
        self.word_blocks = [] # meta info for word in each line/block
        self.ocr_text = [] # OCR'd text
        self.ocr_translated = [] # OCR'd text translated
        self.bounding_boxes = [] # bounding boxes of text lines
        self.space_height = 5 # minimum space height to crop between text lines
        self.is_inverted = False # indicator for text and background color inversion

    def decompose(self):
        """ Use OCR to find bounding boxes of each line in document and dissect 
        into workable parts """
        with PyTessBaseAPI() as api:
            api.SetImage(self.img_file)
            # Interate over lines using OCR
            boxes = api.GetComponentImages(RIL.TEXTLINE, True)
            
            for i, (im, box, _, _) in enumerate(boxes):
                # im is a PIL image object
                # box is a dict with x, y, w and h keys
                api.SetRectangle(box["x"], box["y"], box["w"], box["h"])

                #this tracks all the places that the texture needs to be laid
                self.bounding_boxes.append(box)
                self.ocr_text.append(api.GetUTF8Text())

        if self.translate:
            self.translateText()
        self.space_height = self.getMinSpaceHeight() # get the minimum patch height
        self.generateExpandedPatches() # strip and expand line spaces
        self.cropImageBlocks() # slice original image into lines
        self.getWordBlocks() # get all word meta info per block
        # self.generateFullCompositeImage() # merge everything together

    def expandStrip(self, img_strip):
        """ Expand an image strip using pixel randomization and quilting """
        img_comp = [img_strip]
        for x in range(1, self.spread):
            img_block = self.randomizeStrip(img_strip)
            img_expand = self.mergeImageList(img_block, "horizontal")
            img_comp.append(img_expand)
        
        return self.mergeImageList(img_comp, "vertical")

    def translateText(self):
        """ Translate text that has been OCR'd from this image """
        for text in self.ocr_text:
            trans_text = g_translate(text)
            self.ocr_translated.append(trans_text)

    def generateFullCompositeImage(self):
        """ Merge image blocks with patches to generate complete composite image """
        # merge everything back together to a composite image
        for i in range(0, len(self.img_blocks)):
            if i == 0:
                self.img_comp = self.img_blocks[i]
            else:
                self.img_comp = self.mergeImages(self.img_comp,self.img_patches[i-1],"vertical")
                self.img_comp = self.mergeImages(self.img_comp,self.img_blocks[i],"vertical")

        self.img_comp.save(open('./image_processing/img_comp.jpg', 'w')) # testing

    def getMinSpaceHeight(self):
        """ Find minimum space height - use this for symmetry """
        space_height = 5 # default max space height
        for idx, box in enumerate(self.bounding_boxes):
            if idx == len(self.bounding_boxes)-1:
                break
            if idx == 0:
                if box['y'] > self.line_buffer:
                    new_space_height = box['y']-self.line_buffer
            else:
                new_space_height = (self.bounding_boxes[idx+1]['y']) - (box['y']+box['h'])
                if new_space_height < space_height and new_space_height > 0:
                    space_height = new_space_height
        return space_height
    
    def generateExpandedPatches(self):
        """ Crop space between lines using starting and ending co-ordinates 
        and then expand the strip based on spread """
        tmp = Image.new('RGBA', (self.img_width, self.img_height), (0,0,0,0))
        img = self.img_file.convert("RGBA")

        # Create the expanded patches
        for idx, box in enumerate(self.bounding_boxes):
            # Cut textures for expansion in paper backgrounds
            # Cut between current box and next box +/- a pixel for slack
            if box['y'] <= self.line_buffer:
                # text too close to top of page
                continue
            y_start = box['y']-self.space_height
            y_end = box['y']-self.line_buffer

            expand = True
            # don't need to expand the last patch
            if idx == len(self.bounding_boxes)-1:
                expand = False

            img_patch = self.createNewPatch(img, y_start, y_end, expand)
            self.img_patches.append(img_patch)

    def createNewPatch(self, img, y_start, y_end, expand=True):
        """ Crop, randomize, and expand a strip """
        textureCrop = img.crop((0, y_start, self.img_width, y_end))
        img_strip = self.randomizeStrip(textureCrop)
        img_patch = self.mergeImageList(img_strip)
        img_patch = self.expandStrip(img_patch)
        return img_patch

    def cropImageBlocks(self, pad_bottom=True):
        """ Crop blocks of image entities for recomposition with bottom padding """
        tmp = Image.new('RGBA', (self.img_width, self.img_height), (0,0,0,0))
        # This creates a composite image with the original image and the transparent overlay
        img = Image.alpha_composite(self.img_file.convert("RGBA"), tmp)
        width, height = img.size
        # iterate through the bounding boxes and crop them out accounting for the first and the last chop
        # to keep headers and footers
        for i, box in enumerate(self.bounding_boxes):
            y_end = box['y']+box['h']+self.line_buffer
            if i == 0:
                # check if there is room to make space above first line
                if box['y'] > self.line_buffer:
                    # seperate the header from first block
                    tmpImageCrop = img.crop((0, 0, width, box['y']-self.line_buffer))
                    self.img_blocks.append(tmpImageCrop)            
                    tmpImageCrop = img.crop((0, box['y']-self.line_buffer, width, y_end))
                else:
                    # include the header in first block
                    tmpImageCrop = img.crop((0, 0, width, y_end))                    
            elif i == len(self.bounding_boxes)-1:
                # include footer in last block
                tmpImageCrop = img.crop((0, box['y']-self.line_buffer, width, height))
            else:
                if pad_bottom:
                    # use space between bounding boxes as padding
                    y_end = self.bounding_boxes[i+1]['y']-self.line_buffer
                tmpImageCrop = img.crop((0, box['y']-self.line_buffer, width, y_end))
            self.img_blocks.append(tmpImageCrop)

    #This merges two image files using PIL
    def mergeImages(self, image1, image2, orientation):
        """Merge two images into one, displayed above and below
        :param image1: PIL object
        :param image2: PIL object
        :return: the merged Image object
        """
        (width1, height1) = image1.size
        (width2, height2) = image2.size
        
        mask1 = image1.convert("RGBA")
        mask2 = image2.convert("RGBA")

        if orientation == "vertical":

            result_width = max(width1, width2)
            result_height = height1 + height2

            result = Image.new('RGB', (result_width, result_height))
            result.paste(image1, (0, 0), mask1)
            result.paste(image2, (0, height1), mask2)

        elif orientation == "horizontal":     

            result_width = width1 + width2
            result_height = max(height1, height2)

            result = Image.new('RGB', (result_width, result_height))
            result.paste(image1, (0, 0), mask1)        
            result.paste(image2, (width1, 0), mask2)
        
        return result

    def mergeImageList(self, img_block, orientation="horizontal"):
        """ Iteratively merge a list of PIL image objects """
        compImage = None
        for i in range(0, len(img_block)):
            if len(img_block) > 1:
                if i == 0:
                    compImage = self.mergeImages(img_block[0],img_block[1],orientation)
                elif i > 1:
                    compImage = self.mergeImages(compImage, img_block[i],orientation)
            else:
                # nothing to merge
                compImage = img_block[i]

        return compImage

    def calculateColorDistance(self, color_1, color_2):
        """ Calculates euclidean color distance of two colors not normalized (for simplicity) """
        distance = (color_2[0]-color_1[0])**2 + (color_2[1]-color_1[1])**2 + (color_2[2]-color_1[2])**2
        return distance

    def randomizeStrip(self, im):
        """ Return blocks of randomized pixels in a single strip """
        rgb_im = im.convert('RGB')
        imWidth, imHeight = im.size
        noise = True
        img_block = []
        cut_width = 0        
        for i in range(0,imWidth,self.pixel_cut_width):
            for t in self.line_list:
                if abs(t-i) <= self.noise_threshold:
                    noise = False

            z = []
            pixelList = []
            for y in range(imHeight):
                cut_width = 0                
                for x in range(self.pixel_cut_width):
                    if i+x == imWidth:
                        break
                    cut_width += 1
                    r, g, b = rgb_im.getpixel((i+x, y))
                    pixelList.append(tuple([r,g,b]))

            if cut_width == 0:
                continue

            #Create a new image from random pixel choices
            im2 = Image.new('RGB', (cut_width, imHeight))

            if noise:
                random.shuffle(pixelList)
                
            im2.putdata(pixelList)
            img_block.append(im2)

        return img_block

    def detectLines(self, img):
        """ Use CV2 to estimate vertical line threshold for randomization """
        img_array = np.asarray(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray,50,150,apertureSize = 3)
        
        minLineLength=100
        lines = cv2.HoughLinesP(image=edges,rho=1,theta=np.pi/180, threshold=200,lines=np.array([]), minLineLength=minLineLength,maxLineGap=100)

        a,b,c = lines.shape
        lineLst =[]
        for i in range(a):

            if abs(lines[i][0][0] - lines[i][0][2]) == 0:
                lineLst.append(lines[i][0][0])

            cv2.line(gray, (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3]), (0, 0, 255), 3, cv2.LINE_AA)

        return lineLst

    def getWordInfo(self, image):
        """ Get word boxes with confidence level in an image -
         does not include text for injection protection"""
        img = image.convert("RGB")
        word_boxes = []        
        with PyTessBaseAPI() as api:
            api.SetImage(img)

            boxes = api.GetComponentImages(RIL.WORD, True)
            for i, (im, box, _, _) in enumerate(boxes):
                api.SetRectangle(box["x"], box["y"], box["w"], box["h"])
                text = api.GetUTF8Text()
                conf = api.MeanTextConf()
                word = { "x":box["x"]
                    , "y":box["y"]
                    , "width":box["w"]
                    , "height":box["h"]
                    , "confidence":conf 
                }
                word_boxes.append(word)

        return word_boxes

    def getWordBlocks(self):
        """ Get bounding boxes for single words in a line """
        for img in self.img_blocks:
            word_block = self.getWordInfo(img)
            self.word_blocks.append(word_block)