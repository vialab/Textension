from cStringIO import StringIO
import Image
import urllib

def getMap(name,latitude,longitude,size,zoom):

    url = "http://maps.googleapis.com/maps/api/staticmap?center="+latitude+","+longitude+"&size="+size+"x"+size+"&zoom="+zoom+"&sensor=false"
    buffer = StringIO(urllib.urlopen(url).read())
    image = Image.open(buffer)
    compImage.save(open('/Users/adambradley/Python_Dev/InLineViz/map/map_{}.jpg'.format(name), 'w'))

    #return image
