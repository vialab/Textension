# This is CS205 Final Project
import numpy as np
import math
import scipy
from FindMatches import *
from scipy import ndimage

def SynthTexture(sourceimage, w, synthdim):
    # some variables, w should be an odd number
    MaxErrThreshold=0.3
    sigma=w/6.4
    x,y=np.meshgrid(list(range(-(w-1)/2,(w-1)/2+1)),list(range(-(w-1)/2,(w-1)/2+1)))
    G=(1/(sigma**2*2*np.pi))*np.exp(-(x**2+y**2)/(2*sigma**2))
    nfilled=0
    tofill=synthdim[0]*synthdim[1]-9 # the number of pixels to fill

    synthim=np.ones((synthdim[0],synthdim[1]))*(-1)
    im_filled=np.zeros((synthdim[0],synthdim[1])) # image for testing the original image is filled or not
    offset=(w-1)/2  # offset for zero padding image
    # place the seed in the center and zero padding
    synthim[(math.floor(synthdim[0]/2)-1):(math.floor(synthdim[0])/2+1),\
    (math.floor(synthdim[1]/2)-1):(math.floor(synthdim[1]/2)+1)]=sourceimage[5:7,4:6]
    synthim_padded=np.lib.pad(synthim,(((w-1)/2, (w-1)/2),((w-1)/2, (w-1)/2)),'constant', constant_values=0)
    # find unfilled neighbors
    se= ndimage.generate_binary_structure(2,2)  # use a 3 by 3 structuring element for dilation
    im_filled=(synthim>=0)
    im_dil=ndimage.binary_dilation(im_filled,structure=se)
    [I,J]=np.nonzero(im_dil-im_filled)

    while nfilled<tofill:
        progress=0;
        # get template
        for i in range(0,len(I)):
            template=synthim_padded[I[i]+offset-(w-1)/2:I[i]+offset+(w-1)/2+1,J[i]+offset-(w-1)/2:J[i]+offset+(w-1)/2+1]
            validmask=(template>=0)
            match_list = FindMatches(template, validmask, sourceimage, G)
            BstInd=np.random.randint(0,len(match_list))
            BestMatch=match_list[BstInd][1]
            MatchErr=match_list[BstInd][0]
            if MatchErr<MaxErrThreshold:
                synthim_padded[I[i]+offset,J[i]+offset]=BestMatch
                progress=1
                nfilled=nfilled+1
                im_filled[I[i],J[i]]=1
        if progress==0:
            MaxErrThreshold=MaxErrThreshold*1.1
        im_dil=ndimage.binary_dilation(im_filled,structure=se)
        [I,J]=np.nonzero(im_dil-im_filled)

    synthim=synthim_padded[offset:offset+synthdim[0],offset:offset+synthdim[1]]
    return synthim
