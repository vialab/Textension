from PyPDF2 import PdfFileWriter, PdfFileReader
from io import BytesIO
from wand.image import Image
import os

def pdfSplitPages(fname):
    infile = PdfFileReader(open(fname, 'rb'))
    for i in xrange(infile.getNumPages()):
        p = infile.getPage(i)
        outfile = PdfFileWriter()
        outfile.addPage(p)
        with open('./file_processing/page-%02d.pdf' % i, 'wb') as f:
            outfile.write(f)
    #cleanup the original pdf file in the uploads directory
    os.remove(fname)

def pdfSplitPageStream(file_stream):
    pdf_pages = []
    infile = PdfFileReader(file_stream)
    for i in xrange(infile.getNumPages()):
        tmp = BytesIO()
        p = infile.getPage(i)
        outfile = PdfFileWriter()
        outfile.addPage(p)
        outfile.write(tmp)
        tmp.seek(0)
        img = Image(file=tmp)
        img_blob = img.make_blob(format="jpeg")
        img_bytes = BytesIO(img_blob)
        pdf_pages.append(img_bytes)
    
    return pdf_pages