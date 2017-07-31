from textstat.textstat import textstat

def textConfidence(fname):
    with PyTessBaseAPI() as api:
        #for image in images:
            api.SetImageFile(fname)
            text = api.GetUTF8Text()
            #print api.AllWordConfidences()
            print textstat.flesch_kincaid_grade(text)

            print  textstat.flesch_reading_ease(text)

            print ("90-100 : Very Easy")
            print ("80-89 : Easy")
            print ("70-79 : Fairly Easy")
            print ("60-69 : Standard")
            print ("50-59 : Fairly Difficult")
            print ("30-49 : Difficult")
            print ("0-29 : Very Confusing")
