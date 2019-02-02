import os
# import Textension as iv
import cPickle as pickle
from pdf_page_splitter import *
from ocr_pdf_with_imag_conversion_bounding_boxes import *
from OCR_bounding_boxes_with_confidence import *
from convert_image_to_pdf import *
from pdf_merger import *
from pdf_text_extraction import *
from textConfidence import *
from insertMaps import *


def textProcessing (filename):
    #This strips the text out of an uploaded pdf
    #text = pdf_text_extraction.stripTextFromPDF('./uploads/'+filename)
    #print (text)

    #This splits the uploaded pdf into individual pages
    pdfSplitPages('./uploads/'+filename)

    #This converts all of the spilt pages to jpg cleaning up the file
    #processing folder as it goes it checks for hidden files and ignores them
    for filename2 in os.listdir('./file_processing/'):
        if not filename2.startswith('.'):
            convertPDFToJPG('./file_processing/'+filename2)


    #OCR the image files created and return the dictionary with all the info
    # for filename3 in os.listdir('./file_processing/'):
        # if not filename3.startswith('.'):
            #Extract the text
            #textConfidence('./file_processing/'+filename3)
            #Get the bounding boxes of the document
            #findBoundingBoxesWord('./file_processing/'+filename3)
            # findBoundingBoxesLine('./file_processing/'+filename3, False)
            #insertMaps('./file_processing/'+filename3)
            # vis = iv.InlineViz("./file_processing/"+filename3, _translate=False, _spread=20)
            # vis.decompose()
            # with open("./vis.pkl", "w+") as f:
            #     pickle.dump(vis, f)

    #Turn marked up image back to pdf

    # for filename4 in os.listdir('./file_processing/'):
    #     if not filename4.startswith('.'):
    #         convertImageToPDF('./file_processing/'+filename4)

    #Merge into one pdf
    # pdfMerger('./file_processing/')
