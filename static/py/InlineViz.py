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

class InlineViz:
    """ Inline Viz wrapper object that performs all algorithm functions """
    # Class Variables
    img_comp = None
    img_file = None
    img_patches = []
    img_blocks = []
    img_height = 0.0
    img_width = 0.0
    ocr_text = ""
    ocr_translated = None
    bounding_boxes = []
    nlp = spacy.load("en")
    line_list = None
    spread = 0

    def __init__(self, fname, _translate=False, _spread=0):
        """ Initialize a file to work with """
        self.img_file = Image.open(fname)
        self.img_width, self.img_height = self.img_file.convert("RGBA").size
        self.line_list = lineDetection(fname)
        self.translate = _translate
        self.spread = _spread

    def findBoundingBoxesLine(self, fname):
        """ Use OCR to find bounding boxes of each line in document """
        tmp = Image.new('RGBA', (self.img_width, self.img_height), (0,0,0,0))
        draw = ImageDraw.Draw(tmp)
        img = self.img_file.convert("RGBA")

        with PyTessBaseAPI() as api:
            api.SetImage(self.img_file)
            # Interate over lines using OCR
            boxes = api.GetComponentImages(RIL.TEXTLINE, True)
            
            for i, (im, box, _, _) in enumerate(boxes):
                # im is a PIL image object
                # box is a dict with x, y, w and h keys
                api.SetRectangle(box['x'], box['y'], box['w'], box['h'])

                #this tracks all the places that the texture needs to be laid
                self.bounding_boxes.append(box)
                self.ocr_text = api.GetUTF8Text(

                #This calls the google translate function to translate a line of text for inclusion WORKING
                if self.translate:
                    trans_text = g_translate(self.ocr_text)
                    self.ocr_translated.append(trans_text)

        for idx, box in enumerate(self.bounding_boxes):
            # Cut textures for expansion in paper backgrounds
            # This cuts a number of lines from below the text bounding box.
            textureCrop = img.crop((0, box['y']+box['h']+1, self.img_width, box['y']+box['h']+5))
            img_strip = randomizeStrip(textureCrop, self.line_list)
            img_patch = merge_image_list(img_strip)
            # don't need to expand the last patch
            if idx != len(self.bounding_boxes):
                img_patch = self.expandStrip(img_patch)

            self.img_patches.append(img_patch)

        # This creates a composite image with the original image and the transparent overlay
        img = Image.alpha_composite(img, tmp)
        width, height = img.size

        # iterate through the bounding boxes and crop them out accounting for the first and the last chop
        # to keep headers and footers
        for i, box in enumerate(self.bounding_boxes):
            if i == 0:
                tmpImageCrop = img.crop((0, 0, width, box['y']+box['h']))
            elif i == len(self.bounding_boxes):
                tmpImageCrop = img.crop((0, box['y'], width, height))
            else:
                tmpImageCrop = img.crop((0, box['y'], width, box['y']+box['h']))
            self.img_blocks.append(tmpImageCrop)

        # merge everything back together to a composite image
        for i in range(0, len(self.img_blocks)):
            if i == 0:
                self.img_comp = merge_images(self.img_blocks[i], self.img_patches[i], "vertical")

            else:
                self.img_comp = merge_images(self.img_comp,self.img_blocks[i],"vertical")
                
                if i != len(self.img_blocks):
                    self.img_comp = merge_images(self.img_comp,self.img_patches[i],"vertical")

        self.img_comp.save(open('./image_processing/img_comp.jpg', 'w')) # testing


    def expandStrip(self, img_strip):
        """ Expand an image strip using pixel randomization and quilting """
        img_comp = img_strip
        for x in range(1, self.spread):
            img_block = randomizeStrip(img_strip, self.line_list)
            img_expand = merge_image_list(img_block, "horizontal")
            img_comp = merge_images(img_comp, img_expand, "vertical")
        return img_comp
