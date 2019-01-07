from PyPDF2 import PdfFileWriter, PdfFileReader
from io import BytesIO
from wand.image import Image
from pdf2image import convert_from_path, convert_from_bytes
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
    images = convert_from_bytes(file_stream.read())
    for img in images:
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        pdf_pages.append(img_bytes)
    # infile = PdfFileReader(file_stream)
    # for i in xrange(infile.getNumPages()):
    #     tmp = BytesIO()
    #     p = infile.getPage(i)
    #     outfile = PdfFileWriter()
    #     outfile.addPage(p)
    #     outfile.write(tmp)
    #     tmp.seek(0)
    #     img = Image(file=tmp)
    #     img.convert("jpg")
        
    #     img_bytes = BytesIO()
    #     img.format = "JPEG"
    #     img.save(img_bytes)
    #     pdf_pages.append(img_bytes)  
    return pdf_pages 