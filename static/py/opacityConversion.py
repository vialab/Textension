# This converts the 0-100 confidence level from the OCR into an opacity
# scale from 0-255. I limit the top range to 165 so you can see the word still
def opacityConversion(confidence):
    OldMax = 100
    OldMin = 0
    NewMin = 200
    NewMax = 0

    OldRange = (OldMax - OldMin)
    if OldRange == 0:
        NewValue = NewMin
    else:
        NewRange = (NewMax - NewMin)
        NewValue = (((confidence - OldMin) * NewRange) / OldRange) + NewMin
        return NewValue
