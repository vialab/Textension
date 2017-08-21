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
import base64
import io
import googleMaps as gm
from opacityConversion import *
from math import ceil, floor

class InlineViz:
    """ Inline Viz wrapper object that performs all algorithm functions and 
    interfaces an image into workable components """
    # Class Variables
    img_comp = None
    img_file = None
    nlp = spacy.load("en")

    def __init__(self, stream, _translate=False, _max_size=(1024,1024), _pixel_cut_width=5, _noise_threshold=25, _spread=0, _line_buffer=1, _hi_res=True, _rgb_text=(0,0,0), _rgb_bg=(255,255,255), _anti_alias=True, _map_height=150):
        """ Initialize a file to work with """
        self.max_size = _max_size # maximum size of image for resizing
        self.img_file = Image.open(stream) # image itselfs
        self.img_file.thumbnail(self.max_size, Image.ANTIALIAS) # resize image to maximum size
        self.img_width, self.img_height = self.img_file.convert("RGBA").size # resized width and height
        self.line_list = self.detectLines(self.img_file) # X coordinates for vertical lines
        self.translate = _translate # indicator for translating OCR'd text
        self.spread = _spread # multiplier for strip size
        self.hi_res = _hi_res # pixel shuffling toggle for every iteration of spread        
        self.pixel_cut_width = _pixel_cut_width # horizontal pixel cut size for randomization
        self.noise_threshold = _noise_threshold # vertical line detection threshold
        self.line_buffer = _line_buffer # space buffer cropping between bounding boxes
        self.img_patches = [] # strips between lines of text
        self.img_blocks = [] # lines of text
        self.img_chops = [] # spaces between words
        self.chop_dimension = [] # full dimensions of each chop
        self.img_text = [] # text blocks
        self.word_blocks = [] # meta info for word in each line/block
        self.ocr_text = [] # OCR'd text
        self.ocr_translated = [] # OCR'd text translated
        self.bounding_boxes = [] # bounding boxes of text lines
        self.space_height = 5 # minimum space height to crop between text lines
        self.is_inverted = False # indicator for text and background color inversion
        self.has_header = False # if header is included with first text img block
        self.rgb_text = _rgb_text # text color RGB anchor for background color detection
        self.rgb_bg = _rgb_bg # background color RGB anchor for text color detection
        self.anti_alias = _anti_alias # color sampling for anti-aliasing of artifacts
        self.map_height = _map_height # height of maps for insertion

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
            self.translateText() # translate the text to french
        self.cropImageBlocks() # slice original image into lines
        self.getWordBlocks() # get all word meta info per block
        self.space_height = self.getMinSpaceHeight() # get the minimum patch height        
        self.generateExpandedPatches() # strip and expand line spaces        
        # self.generateFullCompositeImage() # merge everything together

    def expandStrip(self, img_strip):
        """ Expand an image strip using pixel randomization and quilting """
        img_comp = [img_strip]
        pixel_block = self.randomizeStrip(img_strip)
        if len(pixel_block) == 0:
            return img_strip
        if self.anti_alias:
            pixel_block = self.removeArtifacts(pixel_block)

        for x in range(1, self.spread):
            if x > 1 and not self.hi_res:
                img_comp.append(img_expand)
                continue
            img_block = []
            for block in pixel_block:
                #Create a new image from random pixel choices
                img_pixel = Image.new('RGB', (block["cut_width"], img_strip.size[1]))

                if block["noise"]:
                    random.shuffle(block["pixel_list"])
                    
                img_pixel.putdata(block["pixel_list"])
                img_block.append(img_pixel)

            img_expand = self.mergeImageList(img_block, "horizontal")
            img_comp.append(img_expand)
        
        return self.mergeImageList(img_comp, "vertical")

    def removeArtifacts(self, pixel_block):
        aa_block = []
        for block in pixel_block:
            pixel_list = []
            for i, pixel_color in enumerate(block["pixel_list"]):
                if block["noise"] and not self.isBackgroundNoiseColor(pixel_color):
                    new_color = self.getSampledBackgroundColor(i, block["pixel_list"], block["cut_width"])
                    pixel_list.append(new_color)
                else:
                    pixel_list.append(pixel_color)
            aa_block.append({ "pixel_list":pixel_list, "cut_width":block["cut_width"], "noise":block["noise"] })
        return aa_block


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
                self.img_comp = self.img_blocks[i]["img"]
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
                if new_space_height < space_height and new_space_height > self.line_buffer:
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

            if (y_end - y_start) < 1:
                continue

            # if aa enabled, sample a text block to get background and text colors
            if self.anti_alias:
                # get nearest next line sample
                for i in range(idx, len(self.img_text)-1):
                    line_len = len(self.img_text[i])
                    if line_len > 0:
                        # sample the middle word
                        word_idx = int(floor(line_len / 2) - 1)
                        if word_idx < 0:
                            word_idx = 0
                        self.sampleBackgroundTextColor(self.img_text[i][word_idx]["img"])
                        break

            img_patch = self.createNewPatch(img, y_start, y_end, True)
            img_patch = self.getImageDict(img_patch)
            if idx < len(self.img_chops):
                if self.img_chops[idx+1][0]["has_map"]:
                    img_patch["map_height"] = self.map_height
            self.img_patches.append(img_patch)

    def createNewPatch(self, img, y_start, y_end, expand=True):
        """ Crop, randomize, and expand a strip """
        img_patch = img.crop((0, y_start, self.img_width, y_end))
        if expand:
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
            if i != len(self.bounding_boxes)-1:
                if pad_bottom:
                    # use space between bounding boxes as padding
                    y_end = self.bounding_boxes[i+1]['y']-self.line_buffer
                else:
                    # otherwise just go to bottom of bounding box
                    y_end = box['y']+box['h']+self.line_buffer            
            else:
                # last one goes to bottom
                y_end = height

            if i == 0:
                # check if there is room to make space above first line
                if box['y'] > self.line_buffer:
                    # seperate the header from first block
                    self.has_header = True
                    tmpImageCrop = img.crop((0, 0, width, box['y']-self.line_buffer))
                    self.img_blocks.append(self.getImageDict(tmpImageCrop))
                    tmpImageCrop = img.crop((0, box['y']-self.line_buffer, width, y_end))
                else:
                    # include the header in first block
                    tmpImageCrop = img.crop((0, 0, width, y_end))
            else:
                tmpImageCrop = img.crop((0, box['y']-self.line_buffer, width, y_end))
            
            self.img_blocks.append(self.getImageDict(tmpImageCrop))

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
        """ Calculates euclidean color distance modified for perception using weighted RGB color spaces """
        rm = 0.5*(color_1[0]+color_2[0])
        d = ((color_1[0]-color_2[0])**2, (color_1[1]-color_2[1])**2, (color_1[2]-color_2[2])**2)
        d = ((2+rm/256)*d[0], 4*d[1], (2+((255-rm)/256))*d[2])
        d = (d[0]+d[1]+d[2])**0.5
        return d

    def randomizeStrip(self, im):
        """ Return blocks of randomized pixels in a single strip """
        rgb_im = im.convert('RGB')
        imWidth, imHeight = im.size
        img_block = []
        cut_width = 0
        pixel_block = []
        for i in range(0,imWidth,self.pixel_cut_width):
            noise = True
            for t in self.line_list:
                if abs(t-i) <= self.noise_threshold:
                    noise = False

            z = []
            pixel_list = []
            for y in range(imHeight):
                cut_width = 0                
                for x in range(self.pixel_cut_width):
                    if i+x == imWidth:
                        break
                    cut_width += 1
                    r, g, b = rgb_im.getpixel((i+x, y))
                    pixel_list.append((r,g,b))

            if cut_width == 0:
                continue
            pixel_block.append({"pixel_list":pixel_list, "cut_width":cut_width, "noise":noise})

        return pixel_block

    def detectLines(self, img):
        """ Use CV2 to estimate vertical line threshold for randomization """
        img_array = np.asarray(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray,50,150,apertureSize = 3)
        
        minLineLength=100
        lines = cv2.HoughLinesP(image=edges,rho=1,theta=np.pi/180, threshold=200,lines=np.array([]), minLineLength=minLineLength,maxLineGap=100)
        
        if lines is None:
            return []
        
        lineLst =[]            
        a,b,c = lines.shape
        for i in range(a):

            if abs(lines[i][0][0] - lines[i][0][2]) == 0:
                lineLst.append(lines[i][0][0])

            cv2.line(gray, (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3]), (0, 0, 255), 3, cv2.LINE_AA)

        return lineLst

    def getWordInfo(self, idx, image):
        """ Get word boxes with confidence level in an image -
         does not include text for injection protection """
        img = image.convert("RGB")
        word_boxes = []
        bounding_boxes = []
        img_crops = []
        has_map = False
        with PyTessBaseAPI() as api:
            api.SetImage(img)

            boxes = api.GetComponentImages(RIL.WORD, True)
            for i, (im, box, _, _) in enumerate(boxes):
                api.SetRectangle(box["x"], box["y"], box["w"], box["h"])
                text = api.GetUTF8Text()
                if text.strip() == u"":
                    continue
                entities = self.nlp(text)
                conf = api.MeanTextConf()
                label = ""
                if len(entities.ents) > 0:
                    label = entities.ents[-1].label_

                x_start = box['x']-self.line_buffer
                x_end = box['x'] + box['w'] + self.line_buffer
                img_dict = self.getImageDict(img.crop((x_start, 0, x_end, img.size[1])))
                img_crops.append(img_dict)

                word = { "x":box["x"]
                    , "y":box["y"]
                    , "width":box["w"]
                    , "height":box["h"]
                    , "confidence":conf 
                    , "label": label
                }

                if label == "GPE":
                    map_width = self.bounding_boxes[idx]["w"]
                    img_map = gm.getMap(text, map_width, self.map_height)
                    word["map"] = self.encodeBase64(img_map)
                    word["map_x"] = self.bounding_boxes[idx]["x"]
                    has_map = True

                bounding_boxes.append(box)
                word_boxes.append(word)

            self.img_text.append(img_crops)
        return word_boxes, bounding_boxes, has_map

    def chopImageBlockSpace(self, boxes, img):
        """ Crop word spaces in each line """
        width, height = img.size
        x_start = 0
        img_chop = []
        for i, box in enumerate(boxes):
            x_end = box['x']-self.line_buffer
            img_dict = self.getImageDict(img.crop((x_start, 0, x_end, height)))
            img_chop.append(img_dict)
            x_start = box['x'] + box['w'] + self.line_buffer
        
        x_end = width
        if not (x_start < x_end):
            x_start = boxes[-1]['x'] - self.line_buffer
        
        img_dict = self.getImageDict(img.crop((x_start, 0, x_end, height)))
        img_chop.append(img_dict)
                
        return img_chop

    def getWordBlocks(self):
        """ Get bounding boxes for single words in a line """
        for idx, img_dict in enumerate(self.img_blocks):
            img = img_dict["img"]
            word_block, boxes, has_map = self.getWordInfo(idx, img)
            if idx == 0 and self.has_header:
                chop = self.getImageDict(img)
                chop["has_map"] = has_map
                self.img_chops.append([chop,])
            else:
                chops = self.chopImageBlockSpace(boxes, img)
                for chop in chops:
                    chop["has_map"] = has_map
                self.img_chops.append(chops)
            self.chop_dimension.append({"width":img.size[0],"height":img.size[1]})
            self.word_blocks.append(word_block)

    def getImageDict(self, image):
        img_dict = { "img":image
                    , "width":image.size[0]
                    , "height":image.size[1]
                    , "src":self.encodeBase64(image)}
        return img_dict

    def encodeBase64(self, image):
        bImage = io.BytesIO()
        image.save(bImage, format="PNG")
        return base64.b64encode(bImage.getvalue())

    def sampleBackgroundTextColor(self, image):
        """ Returns background color and text color using min color distance from extremes """
        rgb_im = image.convert("RGB")
        width, height = image.size
        _rgb_bg = self.rgb_bg
        _rgb_text = self.rgb_text
        min_bg = 999999
        min_text = 999999

        for y in range(0, height):
            for x in range(0, width):
                r, g, b = rgb_im.getpixel((x, y))
                dist_bg = self.calculateColorDistance((r,g,b), self.rgb_bg)
                dist_text = self.calculateColorDistance((r,g,b), self.rgb_text)
                if dist_bg < min_bg:
                    _rgb_bg = (r,g,b)
                    min_bg = dist_bg
                if dist_text < min_text:
                    _rgb_text = (r,g,b)
                    min_text = dist_text

        self.rgb_bg = _rgb_bg
        self.rgb_text = _rgb_text

    def isBackgroundNoiseColor(self, color):
        """ Test if color closer to bg or text color """
        dist_bg = self.calculateColorDistance(color, self.rgb_bg)
        dist_text = self.calculateColorDistance(color, self.rgb_text)
        if dist_text > (dist_bg)*1.5:
            return True
        else:
            return False

    def calculateAverageColor(self, color_list):
        """ Calculate average RGB values """
        rgb = [sum(color) for color in zip(*color_list)]
        r = rgb[0] / len(color_list)
        g = rgb[1] / len(color_list)
        b = rgb[2] / len(color_list)
        return (r, g, b)

    def getSampledBackgroundColor(self, idx, pixel_list, width):
        """ Find averaged nearest NWSE background colors """
        color_list = []
        W = int(floor(idx/width) * width)
        E = int(ceil(idx/width) * width)
        S = len(pixel_list) - (E - idx)
        # still need to account for edge cases
        if (idx - width) > 0: # N
            for i in range(idx, 0, -width):
                if self.isBackgroundNoiseColor(pixel_list[i]):
                    color_list.append(pixel_list[i])
                    break
        if idx > W: # W
            for i in range(idx, W, -1):
                if self.isBackgroundNoiseColor(pixel_list[i]):
                    color_list.append(pixel_list[i])
                    break
        if E > idx: # E
            for i in range(idx, E):
                if self.isBackgroundNoiseColor(pixel_list[i]):
                    color_list.append(pixel_list[i])
                    break
        if S > idx: # S
            for i in range(idx, S, width):
                if self.isBackgroundNoiseColor(pixel_list[i]):
                    color_list.append(pixel_list[i])
                    break
        
        color_list.append(self.rgb_bg) # bias towards the background color
        return self.calculateAverageColor(color_list)



