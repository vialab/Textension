import PIL
import os

def convertImageToPDF(fname):
    im = PIL.Image.open(fname)
    newfilename = fname+ '.pdf'
    PIL.Image.Image.save(im, newfilename, "PDF", resoultion=100.0)

    #cleanup the trailing image files
    os.remove(fname)
