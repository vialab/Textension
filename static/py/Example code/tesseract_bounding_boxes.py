import tesseract

api = tesseract.TessBaseAPI()
api.Init(".","eng",tesseract.OEM_DEFAULT)
api.SetVariable("tessedit_char_whitelist", "0123456789abcdefghijklmnopqrstuvwxyz")
api.SetPageSegMode(tesseract.PSM_AUTO)

mImgFile = "test.jpg"
mBuffer=open(mImgFile,"rb").read()
result = tesseract.ProcessPagesBuffer(mBuffer,len(mBuffer),api)
print("result(ProcessPagesBuffer)=",result)

#tesseract.GetBoxText() method returns the exact position of each character in an array.

#Besides, there is a command line option tesseract test.jpg result hocr that will generate
#a result.html file with each recognized word's coordinates in it. But I'm not sure whether
#it can be called through python script.
