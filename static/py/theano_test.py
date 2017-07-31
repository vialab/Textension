#Theano GPU tests

#Import an image from PIL
from PIL import Image
image = Image.open('color.png', 'r')

#Turn the image into a numpy array
import numpy
array1 = numpy.asarray(image)


#You may, at this point, specify a data type. For injecting images into Theano, we’ll often want to convert them to float32 to allow GPU processing :
import theano
array1 = numpy.asarray(image, dtype='float32')

#Or for enhanced portability, you can use Theano’s default float datatype (which will be float32 if the code is intended to run in the current generation of GPUs) :
array1 = numpy.asarray(image, dtype=theano.config.floatX)

#Alternatively, the array can be converted from the ImagingCore object :
array2 = numpy.asarray(image.getdata())

#If speed is important to you, do not convert an image from PIL to Numpy like this…
from PIL import Image
import numpy
image = Image.open('color.png', 'r').getdata()
imageArray = numpy.fromstring(image.tostring(), dtype='uint
