#For example, if your input texture file is located at "../textures/" and named as "input_texture.jpg". You want to generate a 200 * 200 image and name it as "output". Then, in your terminal window, you should type:
# python serial_driver.py ../textures/input_texture.jpg output 15 200 200


import numpy as np
from scipy import ndimage
import pylab
from PIL import Image
from SynthTexture import *
import time
import sys

if __name__ == "__main__":

    #read input arguments
    inputfile = sys.argv[1]
    outputfile = sys.argv[2]
    w = int(sys.argv[3])
    syn_size_1 = int(sys.argv[4])
    syn_size_2 = int(sys.argv[5])

    t0 = time.time()
    tex=ndimage.imread(inputfile)
    tex=tex/255.0;
    Sythim=SynthTexture(tex, w, [syn_size_1,syn_size_2])
    print "Serial Version ", time.time()-t0, " seconds"
    im_out=Image.fromarray(Sythim*255)
    im_out.show()
    im_out.convert('RGB').save(outputfile,"JPEG")
