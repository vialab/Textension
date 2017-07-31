import sys

def FindMatches(targetwindow, validMask, sourceimage, G):
	w,h=sourceimage.shape
	n=targetwindow.shape[0]

	ErrThreshold=0.1
	#print validMask
	#print G
	TotWeight=sum(sum(validMask*G))
	SSD=[]
	pixelVal=[]
	# in this implementation, we're not gonna use convolution
	# rather, we're going to use for loop
	for i in range((n-1)/2,w-(n-1)/2):
		for j in range((n-1)/2,h-(n-1)/2):
			dist=(targetwindow-sourceimage[i-(n-1)/2:i+(n+1)/2,j-(n-1)/2:j+(n+1)/2])**2
			SSD.append(sum(sum(dist*validMask*G))/TotWeight)
			pixelVal.append(sourceimage[i,j])

	#print SSD
	MinErr=min(SSD)
	if MinErr<0 and abs(minErr)>1e-15:
		sys.exit("large error encountered!")

	for err in SSD:
		if err<0:
			err=0

	ErrNVal=zip(SSD,pixelVal)
	return [(err, val) for (err, val) in ErrNVal if err<=MinErr*(1+ErrThreshold)]
