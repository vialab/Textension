from io import StringIO
from PIL import Image
import urllib.request, urllib.parse, urllib.error
import json

def getMap(google_key, search, width=150, height=100, zoom=4):
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json?key=" + google_key + "&address=" + search
        geo = json.loads(urllib.request.urlopen(url).read())
        ne = geo["results"][0]["geometry"]["bounds"]["northeast"]
        sw = geo["results"][0]["geometry"]["bounds"]["southwest"]
        lat = ( ne["lat"] + sw["lat"] ) / 2
        lng = ( ne["lng"] + sw["lng"] ) / 2
        height = height + 30
        url = "http://maps.googleapis.com/maps/api/staticmap?key=" + google_key + "&center="+ str(lat-0.5) + "," + str(lng) +"&size="+str(width)+"x"+str(height)+"&zoom="+str(zoom)+"&sensor=false"
        buffer = StringIO(urllib.request.urlopen(url).read())
        image = Image.open(buffer)
        image = image.crop((0,0,image.size[0],image.size[1]-30))
        return image
    except:
        return None