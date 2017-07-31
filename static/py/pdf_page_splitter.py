from PyPDF2 import PdfFileWriter, PdfFileReader
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
