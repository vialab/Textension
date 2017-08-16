from cStringIO import StringIO
from PIL import Image
import urllib

def getMap(search, width=150, height=100, zoom=4):
    url = "http://maps.googleapis.com/maps/api/staticmap?center="+search+"&size="+width+"x"+height+"&zoom="+zoom+"&sensor=false"
    buffer = StringIO(urllib.urlopen(url).read())
    image = Image.open(buffer)
    return image
