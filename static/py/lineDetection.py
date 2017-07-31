import numpy as np
import cv2

def lineDetection(fname):
    gray = cv2.imread(fname)
    edges = cv2.Canny(gray,50,150,apertureSize = 3)
    #cv2.imwrite('/Users/adambradley/Python_Dev/InLineViz/edges-50-150.jpg',edges)
    minLineLength=100
    lines = cv2.HoughLinesP(image=edges,rho=1,theta=np.pi/180, threshold=200,lines=np.array([]), minLineLength=minLineLength,maxLineGap=100)


    a,b,c = lines.shape
    lineLst =[]
    for i in range(a):

        if abs(lines[i][0][0] - lines[i][0][2]) == 0:
            lineLst.append(lines[i][0][0])


        cv2.line(gray, (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3]), (0, 0, 255), 3, cv2.LINE_AA)
    #cv2.imwrite('/Users/adambradley/Python_Dev/InLineViz/houghlines.jpg',gray)
    #print lineLst
    return lineLst
