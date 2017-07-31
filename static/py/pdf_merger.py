from PyPDF2 import PdfFileMerger, PdfFileReader
import os

def pdfMerger(path):

    merger = PdfFileMerger()
    files = [x for x in os.listdir(path) if x.endswith('.pdf')]
    for fname in sorted(files):
        merger.append(PdfFileReader(file(path+fname, 'rb')))
        #merger.append(PdfFileReader(open(os.path.join(path, fname), 'rb')))
        os.remove(path+fname)

    #merger.write("output.pdf")
    merger.write(os.path.join(path, "ocr_document.pdf"))
