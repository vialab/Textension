from tesserocr import PyTessBaseAPI

images = ['sample.jpg', 'sample2.jpg', 'sample3.jpg']

with PyTessBaseAPI() as api:
    for img in images:
        api.SetImageFile(img)
        print api.GetUTF8Text()
        print api.AllWordConfidences()
# api is automatically finalized when used in a with-statement (context manager).
# otherwise api.End() should be explicitly called when it's no longer needed.

#Basic Usage
import tesserocr
from PIL import Image

print tesserocr.tesseract_version()  # print tesseract-ocr version
print tesserocr.get_languages()  # prints tessdata path and list of available languages

image = Image.open('sample.jpg')
print tesserocr.image_to_text(image)  # print ocr text from image
# or
print tesserocr.file_to_text('sample.jpg')


#Advanced API
from PIL import Image
from tesserocr import PyTessBaseAPI

image = Image.open('/usr/src/tesseract/testing/phototest.tif')
with PyTessBaseAPI() as api:
    api.SetImage(image)
    boxes = api.GetComponentImages(RIL.TEXTLINE, True)
    print 'Found {} textline image components.'.format(len(boxes))
    for i, (im, box, _, _) in enumerate(boxes):
        # im is a PIL image object
        # box is a dict with x, y, w and h keys
        api.SetRectangle(box['x'], box['y'], box['w'], box['h'])
        ocrResult = api.GetUTF8Text()
        conf = api.MeanTextConf()
        print (u"Box[{0}]: x={x}, y={y}, w={w}, h={h}, "
               "confidence: {1}, text: {2}").format(i, conf, ocrResult, **box)


#orientation andscript detect_orientation

from PIL import Image
from tesserocr import PyTessBaseAPI, PSM

with PyTessBaseAPI(psm=PSM.AUTO_OSD) as api:
    image = Image.open("/usr/src/tesseract/testing/eurotext.tif")
    api.SetImage(image)
    api.Recognize()

    it = api.AnalyseLayout()
    orientation, direction, order, deskew_angle = it.Orientation()
    print "Orientation: {:d}".format(orientation)
    print "WritingDirection: {:d}".format(direction)
    print "TextlineOrder: {:d}".format(order)
    print "Deskew angle: {:.4f}".format(deskew_angle)

#iterate over classifier choices for a single symbol
from tesserocr import PyTessBaseAPI, RIL, iterate_level

with PyTessBaseAPI() as api:
    api.SetImageFile('/usr/src/tesseract/testing/phototest.tif')
    api.SetVariable("save_blob_choices", "T")
    api.SetRectangle(37, 228, 548, 31)
    api.Recognize()

    ri = api.GetIterator()
    level = RIL.SYMBOL
    for r in iterate_level(ri, level):
        symbol = r.GetUTF8Text(level)  # r == ri
        conf = r.Confidence(level)
        if symbol:
            print u'symbol {}, conf: {}'.format(symbol, conf),
        indent = False
        ci = r.GetChoiceIterator()
        for c in ci:
            if indent:
                print '\t\t ',
            print '\t- ',
            choice = c.GetUTF8Text()  # c == ci
            print u'{} conf: {}'.format(choice, c.Confidence())
            indent = True
        print '---------------------------------------------'
