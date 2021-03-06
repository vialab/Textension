from PIL import Image, ImageDraw, ImageFont
from tesserocr import PyTessBaseAPI, PSM, RIL, OEM
from google_translate import *
import spacy
from generate_examples import *
import os
from CAIS import *
import random
import glob
import numpy as np
import cv2
import imutils
import base64
import io
import googleMaps as gm
import getngrams as ng
import matplotlib as mpl
import math
import colour
mpl.use("Agg")
import matplotlib.pyplot as plt
from opacityConversion import *
from math import ceil, floor

class Block(object):
    """ Inline Viz wrapper object that performs all algorithm functions and 
    interfaces an image into workable components """
    # Class Variables
    img_comp = None
    img_file = None
    nlp = spacy.load("en")

    def __init__(self, _img_file, _translate=False
    , _pixel_cut_width=5, _noise_threshold=25, _vertical_spread=5
    , _horizontal_spread=500, _line_buffer=1, _hi_res=True, _rgb_text=(0,0,0)
    , _rgb_bg=(255,255,255), _anti_alias=True, _map_height=150, _blur=0
    , _google_key="", _coords=(0,0), _block=0, _full_img_width=None):
        """ Initialize a file to work with """
        self.img_file = _img_file # PIL image
        self.img_width, self.img_height = self.img_file.convert("RGBA").size # resized width and height
        self.full_img_width = _full_img_width # width of the full image (all blocks included)
        self.img_coords = _coords # starting coordinates for this block
        self.line_list = self.detectLines(self.img_file) # X coordinates for vertical lines
        self.translate = _translate # indicator for translating OCR'd text
        self.vertical_spread = _vertical_spread # multiplier for strip size
        self.horizontal_spread = _horizontal_spread # multiplier for space size
        self.hi_res = _hi_res # pixel shuffling toggle for every iteration of vertical_spread        
        self.pixel_cut_width = _pixel_cut_width # horizontal pixel cut size for randomization
        self.noise_threshold = _noise_threshold # vertical line detection threshold
        self.line_buffer = _line_buffer # space buffer cropping between bounding boxes
        self.img_patches = [] # strips between lines of text
        self.img_blocks = [] # lines of text
        self.img_space = [] # spaces between actual words
        self.img_patch_space = [] # spaces between words in the space between lines
        self.chop_dimension = [] # full dimensions of each chop
        self.img_text = [] # text blocks
        self.word_blocks = [] # meta info for word in each line/block
        self.ocr_text = [] # OCR'd text
        self.ocr_translated = [] # OCR'd text translated
        self.bounding_boxes = [] # bounding boxes of text lines
        self.ngram_plot = [] # ngram plots
        self.ngram_data = [] # ngram text data for retrieval
        self.space_height = 5 # minimum space height to crop between text lines
        self.is_inverted = False # indicator for text and background color inversion
        self.has_header = False # if header is included with first text img block
        self.rgb_text = _rgb_text # text color RGB anchor for background color detection
        self.rgb_bg = _rgb_bg # background color RGB anchor for text color detection
        self.anti_alias = _anti_alias # color sampling for anti-aliasing of artifacts
        self.map_height = _map_height # height of maps for insertion
        self.blur = _blur # intensity of median blurring for patches
        self.binarize = False # toggle binarization for pre-processing tesseract input
        self.google_key = _google_key # google developer key
        self.idx_block = _block # block number in a Textension object

    def decompose(self):
        """ Use OCR to find bounding boxes of each line in document and dissect 
        into workable parts """
        # img_bw = self.binarizeSharpenImage(self.img_file)
        img_bw = self.img_file
        with PyTessBaseAPI(psm=PSM.SINGLE_BLOCK, oem=OEM.LSTM_ONLY) as api:
            api.SetImage(img_bw)
            # Iterate over lines using OCR
            # img = np.array(self.img_file, dtype=np.uint8)
            boxes = api.GetComponentImages(RIL.TEXTLINE, True)
            y = 0
            h = 0
            for i, (im, box, _, _) in enumerate(boxes):
                # im is a PIL image object
                # box is a dict with x, y, w and h keys

                # because we've already segmented page into blocks
                # assume our lines are full width of the page
                api.SetRectangle(0, box["y"], self.img_width, box["h"])
                self.bounding_boxes.append({"x":0, "y":box["y"], "w":self.img_width, "h":box["h"]})
                api.SetRectangle(box["x"], box["y"], box["w"], box["h"])
                ocr_result = api.GetUTF8Text()
                conf = api.MeanTextConf()
                self.ocr_text.append([ocr_result,conf])
        #         # cv2.rectangle(img, (box["x"],box["y"]), (box["x"]+box["w"],box["y"]+box["h"]),(0,255,0),1)
        # img = Image.fromarray(img)
        # img.show()
        if self.translate and self.google_key != "":
            self.translateText() # translate the text to french
        self.space_height = 1 # get the minimum patch height                    
        self.cropImageBlocks(False) # slice original image into lines
        self.generateExpandedPatches() # strip and expand line spaces
        self.getWordBlocks() # get all word meta info per block
        self.getNgramPlotImageList() # get ngram charts for all our word info
        self.expandWordSpaces() # expand word spaces
        # self.generateFullCompositeImage() # merge everything together

    def getNgramPlotImageList(self, start_date=1800, end_date=2000):
        """ Download list of word usages from google ngrams and save a plot as an image """
        query = ""
        usage_data = {}
        plot_list = {}
        query_set = []
        
        # create full query for google
        for idx, ngram in enumerate(self.ngram_data):
            query_set.append(ngram)
            query = query + ngram["text"] + ","
            # send request every 15 words due to google restraints
            if (idx % 10) == 0 or (idx+1) == len(self.ngram_data):
                query = query.rstrip(",")
                url, url_req, df = ng.getNgrams(query, "eng_2012", start_date, end_date, 3, False)
                # get y values for each dataset
                for ngram in query_set:
                    if ngram["text"] in df.columns:
                        usage_data[ngram["text"]] = df[ngram["text"]].values.tolist()
                # then start a new query set
                query = ""
                query_set = []

        # create years x-axis
        x = list(range(start_date,end_date+1))
        # plot each y value dataset against years
        for ngram in self.ngram_data:
            key = ngram["text"]
            if key not in usage_data:
                continue
            fig = plt.figure(figsize=(1,1), dpi=80)
            plt.plot(x, usage_data[key])                        
            ax = fig.gca()
            ax.axis("off")
            # save figure to image dictionary
            img_bytes = io.BytesIO()
            plt.savefig(img_bytes, format='png', transparent=True)
            plt.close()
            img_bytes.seek(0)
            img_pil = Image.open(img_bytes)
            img_pil = img_pil.resize(ngram["size"], Image.ANTIALIAS)
            plot_list[key] = self.encodeBase64(img_pil)
        # put it all together for front-end use
        for ngram in self.ngram_data:
            key = ngram["text"]
            if key in usage_data:
                img_plot = {
                    "idx_block":ngram["idx_block"]
                    , "idx_word":ngram["idx_word"]
                    , "word_pos":ngram["word_pos"]
                    , "ngram":plot_list[key]
                    , "usage":usage_data[key]
                }
                self.ngram_plot.append(img_plot)

    def expandStrip(self, img_strip):
        """ Expand an image strip using pixel randomization and quilting """
        img_comp = [img_strip]
        pixel_block = self.getPixelBlock(img_strip)
        if len(pixel_block) == 0:
            return img_strip
        if self.anti_alias:
            pixel_block = self.removeArtifacts(pixel_block)

        for x in range(1, self.vertical_spread):
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
        # for text in self.ocr_text:
        #     trans_text = g_translate(text, self.google_key)
        #     self.ocr_translated.append(trans_text)

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
            if idx == 0:
                if box['y'] > self.line_buffer:
                    new_space_height = box['y']-self.line_buffer
            else:
                if idx == len(self.bounding_boxes)-1:
                    break
                new_space_height = (self.bounding_boxes[idx+1]['y']) - (box['y']+box['h'])
                if new_space_height < space_height and new_space_height > self.line_buffer:
                    space_height = new_space_height
        assert space_height > self.line_buffer
        return space_height

    def expandWordSpaces(self):
        """ Analyze and expand spaces between words and keep document 
        justified with relative line width """
        new_img_space = [] # expanded images
        new_img_patch_space = [] # expanded images
        space_count = [len(line) for line in self.img_space] # number of spaces per line
        space_width = [] # total width per line
        # get min space and space width
        for line in self.img_space:
            if len(line) == 0:
                space_width.append(0)
                continue
            line_space = [space["img"].size[0] for space in line]
            total_width = sum(line_space)
            space_width.append(total_width)
        max_stretch = self.horizontal_spread * (self.img_width / self.full_img_width)
        # calculate the largest line width to justify our line towards
        max_width = max([width+max_stretch for idx, width in enumerate(space_width)])
        
        for idx_line, line in enumerate(self.img_space):
            img_space_list = []
            img_patch_space_list = []
            if space_width[idx_line]==0 or space_count[idx_line]==0:
                new_img_space.append([])
                new_img_patch_space.append([])
                continue
            # compare this line to our max and calculate additional 
            # pixels per space on top of pixel spread
            missing_space = max_width-space_width[idx_line]
            add_space = int(floor(missing_space / space_count[idx_line]))
            # round down and add rest of pixels to last space
            extra_space = missing_space - (add_space * space_count[idx_line])

            for idx, space in enumerate(line):
                target_width = space["img"].size[0]+add_space
                if idx == len(line)-1:
                    # make sure we add extra space at end
                    target_width = target_width+extra_space
                # get the pixel data in this space
                rgb_img = space["img"].convert("RGB")
                rgb_img_patch = self.img_patch_space[idx_line][idx]["img"].convert("RGB")
                total_width = space["img"].size[0]
                pixel_list = []
                patch_pixel_list = []
                for y in range(space["img"].size[1]):
                    for x in range(space["img"].size[0]):
                        r, g, b = rgb_img.getpixel((x, y))
                        pixel_list.append((r,g,b))
                for y in range(rgb_img_patch.size[1]):
                    for x in range(rgb_img_patch.size[0]):
                        r, g, b = rgb_img_patch.getpixel((x, y))                        
                        patch_pixel_list.append((r,g,b))
                # shuffle the pixel data and create new image
                img_pixel = Image.new('RGB', (space["img"].size[0], space["img"].size[1]))
                # don't shuffle if space is artificial
                if idx_line > 0 and idx_line < len(self.img_space)-1 and len(self.bounding_boxes[idx_line-1]) > 1:
                    random.shuffle(pixel_list)
                img_pixel.putdata(pixel_list)
                img_list = [img_pixel,]
                # do the same for patch space
                img_patch_pixel = Image.new('RGB', (rgb_img_patch.size[0], rgb_img_patch.size[1]))
                if idx_line > 0 and idx_line < len(self.img_space)-1 and len(self.bounding_boxes[idx_line-1]) > 1:
                    random.shuffle(patch_pixel_list)
                img_patch_pixel.putdata(patch_pixel_list)
                img_patch_list = [img_patch_pixel,]
                # duplicate and reshuffle as required
                last_width = total_width
                while total_width < target_width:
                    if self.hi_res:
                        img_pixel = Image.new('RGB', (space["img"].size[0], space["img"].size[1]))
                        if idx_line > 0 and idx_line < len(self.img_space)-1 and  len(self.bounding_boxes[idx_line-1]) > 1:
                            random.shuffle(pixel_list)                    
                        img_pixel.putdata(pixel_list)
                        # do the same for patch space
                        img_patch_pixel = Image.new('RGB', (rgb_img_patch.size[0], rgb_img_patch.size[1]))
                        if idx_line > 0 and idx_line < len(self.img_space)-1 and  len(self.bounding_boxes[idx_line-1]) > 1:
                            random.shuffle(patch_pixel_list)
                        img_patch_pixel.putdata(patch_pixel_list)

                    img_list.append(img_pixel)
                    img_patch_list.append(img_patch_pixel)
                    total_width = total_width + space["img"].size[0]
                    if total_width == last_width:
                        break # break infinite loop
                    last_width = total_width
                # merge together to get full space image
                img_space = self.mergeImageList(img_list, "horizontal")
                img_patch_space = self.mergeImageList(img_patch_list, "horizontal")
                if total_width > target_width:
                    # crop any excess to match our target width
                    img_space = img_space.crop((0,0,target_width,img_space.size[1]))
                    img_patch_space = img_patch_space.crop((0,0,target_width,img_patch_space.size[1]))
                img_space_list.append(self.getImageDict(img_space))
                img_patch_space_list.append(self.getImageDict(img_patch_space))

            new_img_space.append(img_space_list)
            new_img_patch_space.append(img_patch_space_list)

        self.img_space = new_img_space
        self.img_patch_space = new_img_patch_space

    
    def generateExpandedPatches(self):
        """ Crop space between lines using starting and ending co-ordinates 
        and then expand the strip based on vertical_spread """
        tmp = Image.new('RGBA', (self.img_width, self.img_height), (0,0,0,0))
        img = self.img_file.convert("RGBA")
        # Create the expanded patches
        for idx, box in enumerate(self.bounding_boxes):
            # Cut textures for expansion in paper backgrounds
            # Cut between current box and next box +/- a pixel for slack
            if idx == 0:
                # if we're at the top, take top pixel
                y_start = 0
                y_end = self.space_height
            else:
                y_start = box['y']-(self.space_height+self.line_buffer)
                y_end = box['y']-self.line_buffer

            assert y_end > y_start

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
            img_patch = self.getImageDict(self.smoothImage(img_patch))
            if idx < len(self.img_text)-1:
                if "has_map" in self.img_text[idx+1][0]:
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
        # tmp = Image.new('RGBA', (self.img_width, self.img_height), (0,0,0,0))
        # This creates a composite image with the original image and the transparent overlay
        # img = Image.alpha_composite(self.img_file.convert("RGBA"), tmp)
        img = self.img_file
        width, height = img.size
        if width == 0:
            return
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
                # include the header in first block
                tmpImageCrop = img.crop((0, 0, width, y_end))
            else:
                y_start = box['y']-self.line_buffer
                if box['y'] > self.line_buffer and y_end > y_start:
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

    def getPixelBlock(self, im):
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
        img = img.convert("RGB")
        img_array = np.asarray(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray,50,150,apertureSize = 3)
        
        minLineLength=100
        lines = cv2.HoughLinesP(image=edges,rho=1,theta=np.pi/180, threshold=200,lines=np.array([]), minLineLength=minLineLength,maxLineGap=100)
        
        if lines is None:
            return []
        
        lineLst = []
        a,b,c = lines.shape
        for i in range(a):

            if abs(lines[i][0][0] - lines[i][0][2]) == 0:
                lineLst.append(lines[i][0][0])

            cv2.line(gray, (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3]), (0, 0, 255), 3, cv2.LINE_AA)

        return lineLst

    def getWordInfo(self, idx, image, image_patch):
        """ Get word boxes with confidence level in an image -
         does not include text for injection protection """
        img = image.convert("RGB")
        img_patch = image_patch.convert("RGB")
        word_boxes = []
        img_crops = []
        img_patch_crops = []
        img_spaces = []
        img_patch_spaces = []
        has_map = False
        # img_bw = self.binarizeSharpenImage(image)
        img_bw = image
        x_end = 0
        no_final_space = False
        with PyTessBaseAPI(psm=PSM.SINGLE_LINE, oem=OEM.LSTM_ONLY) as api:
            api.SetImage(img_bw)
            boxes = api.GetComponentImages(RIL.WORD, True)
            for i, (im, box, _, _) in enumerate(boxes):
                # crop the image block for display
                x_start = box["x"]-self.line_buffer
                if i == 0:
                    # first word can take in the left margin
                    x_start = 0
                if i == len(boxes)-1:
                    # Need to create space after last word
                    x_end = box["x"]+box["w"]
                    space_start = x_end+self.line_buffer
                    if space_start >= img.size[0]-self.pixel_cut_width:
                        # impossible to make space after the word..
                        no_final_space = True
                        break
                    else:
                        # try to make a space after the word
                        space_end = space_start + self.pixel_cut_width
                        if space_end > img.size[0]:
                            # make sure we do not cut past the width of the img
                            space_end = img.size[0]-1
                        # cut the space after the word
                        space_crop = self.getImageDict(img.crop((space_start, 0, space_end, img.size[1])))
                        img_spaces.append(space_crop)
                        patch_space_crop = self.getImageDict(img_patch.crop((space_start, 0, space_end, img_patch.size[1])))
                        img_patch_spaces.append(patch_space_crop)
                else:
                    # cut the spaces between the words
                    space_start = box["x"]+box["w"]                    
                    space_end = boxes[i+1][1]["x"]
                    if space_start > space_end:
                        # broken detection.. give up
                        if i > 0:
                            no_final_space = True
                        break
                    x_end = boxes[i+1][1]["x"]-self.line_buffer
                    space_crop = self.getImageDict(img.crop((space_start, 0, space_end, img.size[1])))
                    img_spaces.append(space_crop)
                    patch_space_crop = self.getImageDict(img_patch.crop((space_start, 0, space_end, img_patch.size[1])))
                    img_patch_spaces.append(patch_space_crop)
                    
                # crop out this word from original image
                img_dict = self.getImageDict(img.crop((x_start, 0, x_end, img.size[1])))
                img_crops.append(img_dict)
                # also crop out the same portion from patch above
                img_patch_dict = self.getImageDict(img_patch.crop((x_start, 0, x_end, img_patch.size[1])))
                img_patch_crops.append(img_patch_dict)

                # get the text from within bounding box
                api.SetRectangle(x_start, box["y"], (x_end-x_start), box["h"])
                text = api.GetUTF8Text().strip()
                conf = api.MeanTextConf()
                label = ""

                if text != "":
                    # if we have text to analyze, run entity recognition
                    entities = self.nlp(text)
                    if len(entities.ents) > 0:
                        label = entities.ents[-1].label_

                    # capture other meta info for ngrams
                    ngram = {
                        "idx_block":idx
                        , "idx_word": len(word_boxes)
                        , "word_pos": i
                        , "size":(box["w"],box["h"])
                        , "text":text.strip()
                    }
                    self.ngram_data.append(ngram)
                
                # capture word meta info
                word = { 
                    "idx_block":idx
                    , "word_pos": i
                    , "x":box["x"]
                    , "y":box["y"]
                    , "width":box["w"]
                    , "height":box["h"]
                    , "confidence":conf 
                    , "label": label
                    , "text": text
                }
                if label == "GPE" and self.google_key != "":
                    map_width = self.bounding_boxes[idx]["w"]
                    img_map = gm.getMap(self.google_key, text, map_width, self.map_height)
                    if img_map is not None:
                        word["map"] = self.encodeBase64(img_map)
                        word["map_x"] = self.bounding_boxes[idx]["x"]
                        has_map = True
                word_boxes.append(word)

            # cut the rest of the image off (no text)
            if not no_final_space:
                x_start = x_end
            if x_start < img.size[0]:
                img_crop = self.getImageDict(img.crop((x_start, 0, img.size[0], img.size[1])))
                img_crops.append(img_crop)
                img_crop = self.getImageDict(img_patch.crop((x_start, 0, img.size[0], img_patch.size[1])))
                img_patch_crops.append(img_crop)

        return img_crops, img_patch_crops, img_spaces, img_patch_spaces, word_boxes, has_map

    def chopImageBlockSpace(self, boxes, img):
        """ Crop word spaces in each line """
        width, height = img.size
        x_start = 0
        img_chop = []
        if height == 0 or width == 0:
            return img_chop
        for i, box in enumerate(boxes):
            if i == 0:
                x_start = box["x"] + box["w"]
                continue
            x_end = box["x"]
            if x_end <= x_start:
                continue
            img_dict = self.getImageDict(img.crop((x_start, 0, x_end, height)))
            img_chop.append(img_dict)
            x_start = x_end
        
        x_end = width
        if not (x_start < x_end):
            x_start = boxes[-1]['x'] - self.line_buffer
        if x_start < x_end:
            img_dict = self.getImageDict(img.crop((x_start, 0, x_end, height)))
            img_chop.append(img_dict)
        return img_chop

    def getWordBlocks(self):
        """ Get bounding boxes for single words in a line """
        # Rewritten and removed special cases to simplify
        # First word always includes left margin
        # last word should never be connected to right margin
        for idx, img_dict in enumerate(self.img_blocks):
            img = img_dict["img"]
            self.chop_dimension.append({"width":img.size[0],"height":img.size[1]})
            img_patch = self.img_patches[idx]["img"]
            img_crops, img_patch_crops, img_spaces, img_patch_spaces, word_block, has_map = self.getWordInfo(idx, img, img_patch)
            if has_map:
                for crop in img_crops:
                    crop["has_map"] = True
            if len(img_crops) == 0:
                # if we have no bounding boxes detected (i.e. no images)
                # use original image and make sure everything else is blank too
                img_crops = [[img_dict]]
                img_patch_crops = [[self.getImageDict(img_patch)]]
                img_spaces = []
                img_patch_spaces = []
                word_block = []
            self.word_blocks.append(word_block)
            self.img_text.append(img_crops)
            self.img_space.append(img_spaces)
            self.img_patches[idx] = img_patch_crops
            self.img_patch_space.append(img_patch_spaces)

    def getImageDict(self, image, coords=None):
        img_dict = { "img":image.convert("RGB")
                    , "width":image.size[0]
                    , "height":image.size[1]
                    , "src": self.encodeBase64(image)
                    , "idx_block": self.idx_block}
        if coords:
            img_dict["x"] = coords[0]
            img_dict["y"] = coords[1]
        return img_dict

    def encodeBase64(self, image):
        bImage = io.BytesIO()
        image.save(bImage, format="PNG")

        return base64.b64encode(bImage.getvalue()).decode("utf-8")

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
        r = rgb[0] // len(color_list)
        g = rgb[1] // len(color_list)
        b = rgb[2] // len(color_list)
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

    def binarizeSharpenImage(self, image):
        """ Prepare image for OCR by converting to grayscale, sharpening, and then binarizing """
        image = self.increaseContrast(image)
        if not self.binarize:
            return image.convert("RGB")

        # Read as gray scale
        img_array = np.asarray(image)
        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        # sharpen by multiplying pixels by two
        kernel = np.zeros( (9,9), np.float32)
        kernel[4,4] = 2.0
        box_filter = np.ones( (9,9), np.float32) / 81.0
        kernel = kernel - box_filter
        img_gray = cv2.filter2D(img_gray, -1, kernel)
        # convert from grayscale to black and white
        bw_threshold, img_bw = cv2.threshold(img_gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)        
        img_bw = Image.fromarray(img_bw)
        return img_bw

    def smoothImage(self, image):
        """ Use blurring to smooth an image """
        if self.blur > 0:
            image = image.convert("RGB")
            img_array = np.asarray(image)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            img_cv = cv2.medianBlur(img_cv, self.blur)
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_cv)
            return img_pil
        else:
            return image

    def increaseContrast(self, image):
        """ Increase the contrast of an image to improve OCR results """
        # convert to lab color model
        img_array = np.asarray(image.convert("RGB"))
        lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
        cv2.imshow("lab",lab)

        # split to separate color channels
        l, a, b = cv2.split(lab)

        # apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)

        # merge enhanced L channel back to A B channels
        limg = cv2.merge((cl,a,b))

        # return to RGB channel
        img_cv = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB )
        img_pil = Image.fromarray(img_cv)
        return img_pil

    def deskewImage(self, img):
        """ Ensure that the image is aligned through deskewing """
        # convert the image to grayscale, blur it, and find edges
        # in the image
        image = np.asarray(img)
        orig = image.copy()
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(gray, 75, 200)
        
        # find the contours in the edged image, keeping only the
        # largest ones, and initialize the screen contour
        cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]
        cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5]
        screenCnt = None
        # loop over the contours
        for c in cnts:
            # approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        
            # if our approximated contour has four points, then we
            # can assume that we have found our screen
            if len(approx) == 4:
                screenCnt = approx
                break
        # we could not find four points to deskew
        if screenCnt is None:
            return img

        # show the contour (outline) of the piece of paper
        cv2.drawContours(image, [screenCnt], -1, (0, 255, 0), 2)
        # apply the four point transform to obtain a top-down
        # view of the original image
        warped = self.four_point_transform(orig, screenCnt.reshape(4, 2))
        img_pil = Image.fromarray(warped)
        return img_pil


    def four_point_transform(self, image, pts):
        # obtain a consistent order of the points and unpack them
        # individually
        rect = self.order_points(pts)
        (tl, tr, br, bl) = rect
    
        # compute the width of the new image, which will be the
        # maximum distance between bottom-right and bottom-left
        # x-coordiates or the top-right and top-left x-coordinates
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
    
        # compute the height of the new image, which will be the
        # maximum distance between the top-right and bottom-right
        # y-coordinates or the top-left and bottom-left y-coordinates
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
    
        # now that we have the dimensions of the new image, construct
        # the set of destination points to obtain a "birds eye view",
        # (i.e. top-down view) of the image, again specifying points
        # in the top-left, top-right, bottom-right, and bottom-left
        # order
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype = "float32")
    
        # compute the perspective transform matrix and then apply it
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    
        # return the warped image
        return warped

    def order_points(self, pts):
        # initialzie a list of coordinates that will be ordered
        # such that the first entry in the list is the top-left,
        # the second entry is the top-right, the third is the
        # bottom-right, and the fourth is the bottom-left
        rect = np.zeros((4, 2), dtype = "float32")
        # the top-left point will have the smallest sum, whereas
        # the bottom-right point will have the largest sum
        s = pts.sum(axis = 1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        # now, compute the difference between the points, the
        # top-right point will have the smallest difference,
        # whereas the bottom-left will have the largest difference
        diff = np.diff(pts, axis = 1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        # return the ordered coordinates
        return rect


class Textension(Block):
    def __init__(self, stream, _translate=False, _max_size=(1024,1024)
    , _pixel_cut_width=5, _noise_threshold=25, _vertical_spread=5
    , _horizontal_spread=500, _line_buffer=1, _hi_res=True, _rgb_text=(0,0,0)
    , _rgb_bg=(255,255,255), _anti_alias=True, _map_height=150, _blur=0
    , _google_key="", _margin_size=100, _stripe_bg=False, _blockify_page=True):
        """ Initialize a file to work with """
        # convert uploaded stream to PIL image
        self.img_file = Image.open(stream).convert("RGB") # image itself
        # self.img_file = self.deskewImage(self.img_file)
        original = [float(d) for d in self.img_file.size]
        scale = 300/72.0
        if scale != 1:
            self.img_file.thumbnail([round(scale * d) for d in original], Image.ANTIALIAS)
        self.img_file.thumbnail(_max_size, Image.ANTIALIAS) # resize image to maximum size
        # instantiate our algorithm
        super(Textension, self).__init__(self.img_file, _translate
        , _pixel_cut_width, _noise_threshold, _vertical_spread
        , _horizontal_spread, _line_buffer, _hi_res, _rgb_text
        , _rgb_bg, _anti_alias, _map_height, _blur
        , _google_key)
        self.block_bounds = [[9999, 9999], [0, 0]] # box coords by which all blocks reside
        self.bg_color = (255,255,255) # the background color of the HTML stage
        self.x_mesh = [] # x coords for page block columns 
        self.y_mesh = [] # y coords for page block rows
        self.mesh = [] # two dim array of page block images
        self.block_boxes = [] # detected blocks using tesserocr
        self.blocks = [] # recursed textension objects of each block on the page
        self.margin_size = _margin_size # size of the margin
        self.stripe_bg = _stripe_bg # use vertical gradient to fill blocks
        self.blockify_page = _blockify_page # capture and decompose multiple blocks

    def blockify(self):
        if self.margin_size > 0:
            self.expandMargin(self.margin_size) # expand the margins for infinite canvas
        self.chopPageByBlock()
        for i, (img, box, _, _) in enumerate(self.block_boxes):
            b = Block(img, self.translate, self.pixel_cut_width
            , self.noise_threshold, self.vertical_spread, self.horizontal_spread
            , self.line_buffer, self.hi_res, self.rgb_text, self.rgb_bg
            , self.anti_alias, self.map_height, self.blur, self.google_key
            , _coords=(box["x"],box["y"]), _block=i, _full_img_width=self.img_width)
            b.decompose()
            self.blocks.append(b)

    def linearGradient(self, s, f, n=10):
        """ returns a gradient list of (n) colors between
            two hex colors. start_hex and finish_hex
            should be the full six-digit color string,
            inlcuding the number sign ("#FFFFFF") """
        # Initilize a list of the output colors with the starting color
        RGB_list = [s]
        # Calcuate a color at each evenly spaced value of t from 1 to n
        for t in range(1, n):
            # Interpolate RGB vector for color at the current value of t
            curr_vector = tuple([
            int(s[j] + (float(t)/(n-1))*(f[j]-s[j]))
            for j in range(3)
            ])
            # Add it to our list of output colors
            RGB_list.append(curr_vector)
        return RGB_list

    def fadeColor(self, c, d=1, n=100):
        """ Return a list of colors reducing in opacity """
        color_list = []
        a = 0
        s = int(round(255.0 / n))
        if d < 0:
            s = s * -1
            a = 255
        for i in range(n):
            a=a+s
            if a < 0:
                a = 0
            if a > 255:
                a = 255
            color_list.append((c[0],c[1],c[2],a))
        return color_list

    def stretchFadePixel(self, start_c, end_c, size, px=100):
        """ Linearly fade a single pixel from one color to another """
        strip = Image.new('RGB', size)
        color_list = self.linearGradient(start_c, end_c, px)
        strip.putdata(color_list)
        return strip, color_list

    def pasteFade(self, img, color_list, px=100, d=1, r=0):
        """ Paste a gradient image on top of another 
            based on a list of colours """
        temp = Image.new(mode='RGBA',size=(px,px))
        t_fade = []
        for c in color_list:
            t_fade = t_fade + self.fadeColor(c, d)
        temp.putdata(t_fade)
        if r > 0:
            temp = temp.rotate(r)
        img.paste(temp,(0,0),mask=temp)
        return img

    def createFilledBoxImage(self, c, size):
        """ Returns a blank image with a background color"""
        img = Image.new(mode='RGB',size=size)
        img.paste(c,(0,0,size[0],size[1]))
        img.convert("RGBA")
        return img

    def expandMargin(self, px=100):
        """ Create an expanded background image by expanding the 4 margins 
        to be used on our infinite canvas """
        img = self.img_file.convert("RGB")
        r_total = 0
        g_total = 0
        b_total = 0
        # get the bordering pixels
        top = img.crop((0,0,self.img_width,1))
        right = img.crop((self.img_width-1,0,self.img_width,self.img_height))
        bottom = img.crop((0,self.img_height-1,self.img_width,self.img_height))
        left = img.crop((0,0,1,self.img_height))
        color_list = []
        # aggregate all pixel colors into a list to calculate average
        for x in range(self.img_width-1):
            r, g, b = top.getpixel((x, 0))
            color_list.append((r,g,b))
            r, g, b = bottom.getpixel((x, 0))
            color_list.append((r,g,b))
        for y in range(self.img_height-1):
            r, g, b = right.getpixel((0, y))
            color_list.append((r,g,b))
            r, g, b = left.getpixel((0, y))
            color_list.append((r,g,b))
        self.bg_color = self.calculateAverageColor(color_list)
        if self.bg_color == (255,255,255):
            return
        # now iterate through every pixel and stretch it px pixels
        # our fade will go towards the average colour so that we can use
        # a solid background colour in page
        top_list = []
        bottom_list = []
        right_list = []
        left_list = []
        # these are for the corners that don't have pixels
        tl = self.createFilledBoxImage(self.bg_color, (px,px))
        tr = self.createFilledBoxImage(self.bg_color, (px,px))
        bl = self.createFilledBoxImage(self.bg_color, (px,px))
        br = self.createFilledBoxImage(self.bg_color, (px,px))
        # stretch the top and bottom pixels of the page
        for x in range(self.img_width):
            # top
            r,g,b = top.getpixel((x,0))
            strip, top_colors = self.stretchFadePixel(self.bg_color, (r,g,b), (1,100))
            top_list.append(strip)
            #bottom
            r,g,b = bottom.getpixel((x,0))
            strip, bottom_colors = self.stretchFadePixel((r,g,b), self.bg_color, (1,100))
            bottom_list.append(strip)
        #stretch the right and left pixels of the page
        for y in range(self.img_height):
            #right
            r,g,b = right.getpixel((0,y))
            strip, right_colors = self.stretchFadePixel((r,g,b), self.bg_color, (100,1))
            right_list.append(strip)
            # left
            r,g,b = left.getpixel((0,y))
            strip, left_colors = self.stretchFadePixel(self.bg_color, (r,g,b), (100,1))
            left_list.append(strip)
            # Take the top pixels and fade them upwards (for the corners)
            if y == 0:
                tr = self.pasteFade(tr, right_colors, r=180)
                tl = self.pasteFade(tl, left_colors, r=-90)
            # Take the bottom pixels and fade them downwards (for the corners)
            if y == self.img_height-1:
                br = self.pasteFade(br, right_colors, d=-1, r=-90)
                bl = self.pasteFade(bl, left_colors, d=-1, r=180)
        # merge it all together
        new_top = self.mergeImageList([tl] + top_list + [tr]) 
        new_bottom = self.mergeImageList([bl] + bottom_list + [br])
        new_right = self.mergeImageList(right_list, "vertical")
        new_left = self.mergeImageList(left_list, "vertical")
        middle = self.mergeImageList([new_left, img, new_right])
        self.img_file = self.mergeImageList([new_top, middle, new_bottom], "vertical")
        self.img_width = self.img_file.size[0]
        self.img_height = self.img_file.size[1]

    def boxesOverlap(self, box_a, box_b):
        """ Return true if box a and b overlap """
        a_dx = box_a["x"] + box_a["w"]
        a_dy = box_a["y"] + box_a["h"]
        b_dx = box_b["x"] + box_b["w"]
        b_dy = box_b["y"] + box_b["h"]
        if box_a["x"] >= b_dx or a_dx <= box_b["x"] \
        or box_a["y"] >= b_dy or a_dy <= box_b["y"]:
            return False
        return True

    def justifyBlocks(self, boxes, margin=5):
        """ If there are boundaries that are near each other, cluster them.
            However, only cluster if it makes our bounding box larger """
        for i,box in enumerate(boxes):
            changed = True
            count = 0
            orig_box = box
            while changed:
                changed = False
                if count > 100:
                    break
                for b in boxes:
                    idx = orig_box["x"]+orig_box["w"]
                    idy = orig_box["y"]+orig_box["h"]
                    dx = b["x"]+b["w"]
                    dy = b["y"]+b["h"]

                    xdiff = orig_box["x"]-b["x"]
                    wdiff = dx-idx
                    ydiff = orig_box["y"]-b["y"]
                    hdiff = dy-idy

                    if xdiff > 0 and xdiff <= margin:
                        orig_box["x"] = b["x"]
                        orig_box["w"] = orig_box["w"] + xdiff
                        changed = True
                    if wdiff > 0 and wdiff <= margin:
                        orig_box["w"] = orig_box["w"] + wdiff
                        changed = True
                    if ydiff > 0 and ydiff <= margin:
                        orig_box["y"] = b["y"]
                        orig_box["h"] = orig_box["h"] + ydiff
                        changed = True
                    if hdiff > 0 and hdiff <= margin:
                        orig_box["h"] = orig_box["h"] + hdiff
                        changed = True
                if not changed:
                    boxes[i] = orig_box
                count += 1                

    def chopPageByBlock(self):
        with PyTessBaseAPI(oem=OEM.LSTM_ONLY) as api:
            api.SetImage(self.img_file)
            # Iterate over blocks using OCR
            self.block_boxes = api.GetComponentImages(RIL.BLOCK, True)

        boxes = [box[1] for box in self.block_boxes]
        margin = 2
        for i, box in enumerate(boxes):
            if boxes[i]["x"] > margin and boxes[i]["x"]+boxes[i]["w"] < self.img_width-margin:
                boxes[i]["x"] = boxes[i]["x"]-margin
                boxes[i]["w"] = boxes[i]["w"]+(margin*2)
            if boxes[i]["y"] > margin and boxes[i]["y"]+boxes[i]["h"] < self.img_height-margin:
                boxes[i]["y"] = boxes[i]["y"]-margin
                boxes[i]["h"] = boxes[i]["h"]+(margin*2)

        self.justifyBlocks(boxes, margin)
        # img = np.array(self.img_file, dtype=np.uint8)
        for i, box in enumerate(boxes):
            # box is a dict with x, y, w and h keys
            dx = box["x"]+box["w"]
            dy = box["y"]+box["h"]
            # box all the boxes so that we can track margin
            if box["x"] < self.block_bounds[0][0]:
                self.block_bounds[0][0] = box["x"]
            if box["y"] < self.block_bounds[0][1]:
                self.block_bounds[0][1] = box["y"]
            if dx > self.block_bounds[1][0]:
                self.block_bounds[1][0] = dx
            if dy > self.block_bounds[1][1]:
                self.block_bounds[1][1] = dy
            if self.blockify_page:
                self.y_mesh.append(box["y"])
                self.y_mesh.append(dy)
                self.x_mesh.append(box["x"])
                self.x_mesh.append(dx)
                self.block_boxes[i] = list(self.block_boxes[i])
                self.block_boxes[i][1] = boxes[i]
                self.block_boxes[i][0] = self.img_file.crop((box["x"],box["y"],dx,dy))
        #     cv2.rectangle(img, (box["x"],box["y"]), (box["x"]+box["w"],box["y"]+box["h"]),(0,255,0),1)
        # cv2.rectangle(img, tuple(self.block_bounds[0]), tuple(self.block_bounds[1]),(255,0,0),1)
        # img = Image.fromarray(img)
        # img.show()
        if not self.blockify_page:
            self.x_mesh.append(self.block_bounds[0][0])
            self.y_mesh.append(self.block_bounds[0][1])
            x = self.block_bounds[0][0]
            y = self.block_bounds[0][1]
            dx = self.block_bounds[1][0]
            dy = self.block_bounds[1][1]
            full_block = self.img_file.crop((x,y,dx,dy))
            self.block_boxes = [[full_block, {"x":x,"y":y,"w":dx-x,"h":dy-y}, 0, 0]]
        if self.margin_size > 0:
            self.x_mesh.append(self.margin_size)
            self.x_mesh.append(self.img_width-self.margin_size)
            self.y_mesh.append(self.margin_size)
            self.y_mesh.append(self.img_height-self.margin_size)
        self.x_mesh.append(self.block_bounds[1][0])
        self.x_mesh.append(self.img_width)
        self.y_mesh.append(self.block_bounds[1][1])
        self.y_mesh.append(self.img_height)
        self.x_mesh = set(self.x_mesh)
        self.y_mesh = set(self.y_mesh)
        last_y = 0
        last_x = 0
        for i, y in enumerate(sorted(self.y_mesh)):
            row = []
            for x in sorted(self.x_mesh):
                overlap = False
                for j, b in enumerate(boxes):
                    if self.boxesOverlap(b, {"x":last_x, "y":last_y, "w":x-last_x, "h":y-last_y}):
                        overlap = True
                        self.idx_block = j
                        break
                cell_img = self.img_file.crop((last_x,last_y,x,y))
                if overlap:
                    if self.stripe_bg:
                        cell_strips = []
                        for i in range(cell_img.size[0]):
                            start_c = tuple(cell_img.getpixel((i,0)))
                            end_c = tuple(cell_img.getpixel((i,cell_img.size[1]-1)))
                            strip, _ = self.stretchFadePixel(start_c, end_c, (1,cell_img.size[1]), cell_img.size[1])
                            cell_strips.append(strip)
                        cell = self.getImageDict(self.mergeImageList(cell_strips), (last_x, last_y))
                    else:
                        new_box = self.createFilledBoxImage(self.bg_color, (cell_img.size[0],cell_img.size[1]))
                        cell = self.getImageDict(new_box, (last_x, last_y))
                    cell["background"] = False
                    cell["idx_box"] = j
                else:
                    cell = self.getImageDict(cell_img, (last_x, last_y))
                    cell["background"] = True
                row.append(cell)
                last_x = x
            self.mesh.append(row)
            last_y = y
            last_x = 0