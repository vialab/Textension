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
import getngrams as ng
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from opacityConversion import *
from math import ceil, floor

class InlineViz:
    """ Inline Viz wrapper object that performs all algorithm functions and 
    interfaces an image into workable components """
    # Class Variables
    img_comp = None
    img_file = None
    nlp = spacy.load("en")

    def __init__(self, stream, _translate=False, _max_size=(1024,1024), _pixel_cut_width=5, _noise_threshold=25, _vertical_spread=5, _horizontal_spread=5, _line_buffer=1, _hi_res=True, _rgb_text=(0,0,0), _rgb_bg=(255,255,255), _anti_alias=True, _map_height=150, _blur=0, _google_key=""):
        """ Initialize a file to work with """
        self.max_size = _max_size # maximum size of image for resizing
        self.img_file = Image.open(stream) # image itself
        self.img_file.thumbnail(self.max_size, Image.ANTIALIAS) # resize image to maximum size
        self.img_width, self.img_height = self.img_file.convert("RGBA").size # resized width and height
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
        self.img_space = [] # spaces between words
        self.img_patch_space = [] # spaces between words
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

    def decompose(self):
        """ Use OCR to find bounding boxes of each line in document and dissect 
        into workable parts """
        img_bw = self.binarizeSharpenImage(self.img_file)

        with PyTessBaseAPI() as api:
            api.SetImage(img_bw)
            # Interate over lines using OCR
            boxes = api.GetComponentImages(RIL.TEXTLINE, True)
            
            for i, (im, box, _, _) in enumerate(boxes):
                # im is a PIL image object
                # box is a dict with x, y, w and h keys
                api.SetRectangle(box["x"], box["y"], box["w"], box["h"])

                #this tracks all the places that the texture needs to be laid
                self.bounding_boxes.append(box)
                self.ocr_text.append(api.GetUTF8Text())

        if self.translate and self.google_key != "":
            self.translateText() # translate the text to french
        self.space_height = self.getMinSpaceHeight() # get the minimum patch height                    
        self.cropImageBlocks() # slice original image into lines
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
        for text in self.ocr_text:
            trans_text = g_translate(text, self.google_key)
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

    def expandWordSpaces(self):
        """ Analyze and expand spaces between words and keep document 
        justified with relative line width """
        new_img_space = [] # expanded images
        new_img_patch_space = [] # expanded images
        space_count = [len(line) for line in self.img_space] # number of spaces per line
        space_width = [] # total width per line
        min_space = 999 # amount of generated space to create at a time
        # get min space and space width
        for line in self.img_space:
            if len(line) == 0:
                space_width.append(0)
                continue
            line_space = [space.size[0] for space in line]
            min_line_space = min(line_space)
            total_width = sum(line_space)
            space_width.append(total_width)
            if min_line_space < min_space:
                min_space = min_line_space
        # how much space we want to create at a minimum
        pixel_spread = self.horizontal_spread * min_space
        # calculate the largest line width to justify our line towards
        max_width = max([width+(space_count[idx]*pixel_spread) for idx, width in enumerate(space_width)])
        
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
                target_width = space.size[0]+add_space
                if idx == len(line)-1:
                    # make sure we add extra space at end
                    target_width = target_width+extra_space
                # get the pixel data in this space
                rgb_img = space.convert("RGB")
                if idx_line == 0:
                    rgb_img_patch = self.img_patch_space[idx_line+1][idx].convert("RGB")
                else:
                    rgb_img_patch = self.img_patch_space[idx_line-1][idx].convert("RGB")
                total_width = space.size[0]
                pixel_list = []
                patch_pixel_list = []
                for y in range(space.size[1]):
                    for x in range(space.size[0]):
                        r, g, b = rgb_img.getpixel((x, y))
                        pixel_list.append((r,g,b))
                for y in range(rgb_img_patch.size[1]):
                    for x in range(rgb_img_patch.size[0]):
                        r, g, b = rgb_img_patch.getpixel((x, y))                        
                        patch_pixel_list.append((r,g,b))
                # shuffle the pixel data and create new image
                img_pixel = Image.new('RGB', (space.size[0], space.size[1]))
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
                        img_pixel = Image.new('RGB', (space.size[0], space.size[1]))
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
                    total_width = total_width + space.size[0]
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
            img_patch = self.getImageDict(self.smoothImage(img_patch))
            if idx < len(self.img_text):
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
        tmp = Image.new('RGBA', (self.img_width, self.img_height), (0,0,0,0))
        # This creates a composite image with the original image and the transparent overlay
        img = Image.alpha_composite(self.img_file.convert("RGBA"), tmp)
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
        if idx > 0:
            img_patch = image_patch.convert("RGB")
        word_boxes = []
        img_crops = []
        img_patch_crops = []
        img_spaces = []
        img_patch_spaces = []
        has_map = False
        img_bw = self.binarizeSharpenImage(image)
        single_box_space = False

        with PyTessBaseAPI() as api:
            api.SetImage(img_bw)
            boxes = api.GetComponentImages(RIL.WORD, True)
            for i, (im, box, _, _) in enumerate(boxes):
                # crop the image block for display
                x_start = box["x"]-self.line_buffer
                if i == 0:
                    x_start = 0
                    
                if i == len(boxes)-1:
                    if len(boxes)==1:
                        x_end = box["x"]+box["w"]+self.line_buffer
                    else:
                        x_end = img.size[0]
                else:
                    x_end = boxes[i+1][1]["x"]-self.line_buffer

                if x_end < x_start:
                    # ran into overlapping boxes problems so include rest of image in crop and break
                    x_end = img.size[0]
                    img_dict = self.getImageDict(img.crop((x_start, 0, x_end, img.size[1])))
                    img_crops.append(img_dict)
                    if idx > 0:
                        img_patch_dict = self.getImageDict(img_patch.crop((x_start, 0, x_end, img_patch.size[1])))
                        img_patch_crops.append(img_patch_dict)
                    break

                if len(boxes)==1:
                    # if we have only one bounding box
                    # try to make a space after the word
                    space_start = x_end
                    space_end = space_start + self.pixel_cut_width
                    if space_end > img.size[0]:
                        space_end = img.size[0]
                    if space_start < space_end:
                        space_crop = img.crop((space_start, 0, space_end, img.size[1]))
                        img_spaces.append(space_crop)
                        single_box_space = True
                        if idx > 0:
                            patch_space_crop = img_patch.crop((space_start, 0, space_end, img_patch.size[1]))
                            img_patch_spaces.append(patch_space_crop)
                    else:
                        x_end = img.size[0]

                if i < len(boxes)-1:
                    # cut the spaces between the words
                    space_start = box["x"]+box["w"]                    
                    space_end = boxes[i+1][1]["x"]
                    space_crop = img.crop((space_start, 0, space_end, img.size[1]))
                    img_spaces.append(space_crop)
                    if idx > 0:
                        patch_space_crop = img_patch.crop((space_start, 0, space_end, img_patch.size[1]))
                        img_patch_spaces.append(patch_space_crop)
                # get the text from within bounding box
                api.SetRectangle(x_start, box["y"], (x_end-x_start), box["h"])
                text = api.GetUTF8Text()
                # crop out this word from original image
                img_dict = self.getImageDict(img.crop((x_start, 0, x_end, img.size[1])))
                img_crops.append(img_dict)
                if idx > 0:
                    # also crop out the same portion from patch above
                    img_patch_dict = self.getImageDict(img_patch.crop((x_start, 0, x_end, img_patch.size[1])))
                    img_patch_crops.append(img_patch_dict)

                if text.strip() == u"":
                    continue

                # if we have text to analyze, run entity recognition
                entities = self.nlp(text)
                conf = api.MeanTextConf()
                label = ""
                if len(entities.ents) > 0:
                    label = entities.ents[-1].label_

                # capture other meta info for ngrams
                ngram = {
                    "idx_block":idx
                    , "idx_word": len(word_boxes)
                    , "word_pos": i
                    , "size":(box["w"],((self.space_height - self.line_buffer) * self.vertical_spread))
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
                    , "text": text.strip()
                }
                if label == "GPE":
                    map_width = self.bounding_boxes[idx]["w"]
                    img_map = gm.getMap(text, map_width, self.map_height)
                    if img_map is not None:
                        word["map"] = self.encodeBase64(img_map)
                        word["map_x"] = self.bounding_boxes[idx]["x"]
                        has_map = True
                word_boxes.append(word)

            if len(boxes)==1 and single_box_space:
                # if only one bounding box crop rest of image without text
                x_start = boxes[0][1]["x"]+boxes[0][1]["w"]+self.line_buffer
                x_end = img.size[0]
                img_crop = self.getImageDict(img.crop((x_start, 0, x_end, img.size[1])))
                img_crops.append(img_crop)
                img_crop = self.getImageDict(img_patch.crop((x_start, 0, x_end, img_patch.size[1])))
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
        for idx, img_dict in enumerate(self.img_blocks):
            img = img_dict["img"]
            img_patch = None
            if idx > 0:
                img_patch = self.img_patches[idx-1]["img"]
            if idx == 1:
                # bring first image along for the ride
                img_patch = self.mergeImages(self.img_blocks[0]["img"], img_patch, "vertical")
            img_crops, img_patch_crops, img_spaces, img_patch_spaces, word_block, has_map = self.getWordInfo(idx, img, img_patch)
            if idx == 1:
                # split first image from patch
                new_patch_crops = []
                prev_img_crops = []
                prev_height = self.img_blocks[0]["img"].size[1]
                for crop in img_patch_crops:
                    img_patch_crop = crop["img"].crop((0,prev_height,crop["img"].size[0],crop["img"].size[1]))
                    new_patch_crops.append(self.getImageDict(img_patch_crop))
                    img_crop = crop["img"].crop((0,0,crop["img"].size[0], prev_height))
                    prev_img_crops.append(self.getImageDict(img_crop))
                img_patch_crops = new_patch_crops
                self.img_text[0] = prev_img_crops
                # split first image from space
                new_patch_spaces = []
                prev_img_spaces = []
                for crop in img_patch_spaces:
                    img_patch_crop = crop.crop((0,prev_height,crop.size[0],crop.size[1]))
                    new_patch_spaces.append(img_patch_crop)
                    img_crop = crop.crop((0,0,crop.size[0], prev_height))
                    prev_img_spaces.append(img_crop)
                img_patch_spaces = new_patch_spaces
                self.img_space[0] = prev_img_spaces

            if has_map:
                for crop in img_crops:
                    crop["has_map"] = True
            if len(img_crops) == 0:
                # if we have no bounding boxes detected (i.e. no images)
                # use original image
                img_crops.append(img_dict)
            self.chop_dimension.append({"width":img.size[0],"height":img.size[1]})
            self.word_blocks.append(word_block)
            self.img_text.append(img_crops)
            self.img_space.append(img_spaces)
            if idx > 0:
                self.img_patches[idx-1] = img_patch_crops
                self.img_patch_space.append(img_patch_spaces)

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

    def binarizeSharpenImage(self, image):
        """ Prepare image for OCR by converting to grayscale, sharpening, and then binarizing """
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