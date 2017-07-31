from PIL import Image

#Find the orientation of a text that is passed as an image
def orientation(fname):
    with PyTessBaseAPI(psm=PSM.AUTO_OSD) as api:
        image = Image.open(fname)
        api.SetImage(image)
        api.Recognize()

        it = api.AnalyseLayout()
        orientation, direction, order, deskew_angle = it.Orientation()
        print "Orientation: {:d}".format(orientation)
        print "WritingDirection: {:d}".format(direction)
        print "TextlineOrder: {:d}".format(order)
        print "Deskew angle: {:.4f}".format(deskew_angle)
