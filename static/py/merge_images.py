from PIL import Image, ImageDraw

#This merges two image files using PIL
def merge_images(file1, file2, orientation):
    """Merge two images into one, displayed above and below
    :param file1: path to first image file
    :param file2: path to second image file
    :return: the merged Image object
    """

    if file1 == "/Users/adambradley/Python_Dev/InLineViz/image_processing/.DS_Store" or file1 == "/Users/adambradley/Python_Dev/InLineViz/img_patches/tmp/.DS_Store":
        return None

    elif orientation == "vertical":

        image1 = Image.open(file1)
        image2 = Image.open(file2)

        (width1, height1) = image1.size
        (width2, height2) = image2.size

        result_width = max(width1, width2)
        result_height = height1 + height2

        result = Image.new('RGB', (result_width, result_height))
        mask1 = image1.convert("RGBA")
        mask2 = image2.convert("RGBA")

        result.paste(image1, (0, 0), mask1)
        result.paste(image2, (0, height1), mask2)

        return result

    elif orientation == "horizontal":

        image1 = Image.open(file1)
        image2 = Image.open(file2)

        (width1, height1) = image1.size
        (width2, height2) = image2.size

        result_width = width1 + width2
        result_height = max(height1, height2)

        result = Image.new('RGB', (result_width, result_height))
        mask1 = image1.convert("RGBA")
        mask2 = image2.convert("RGBA")

        result.paste(image1, (0, 0), mask1)
        result.paste(image2, (width1, 0), mask2)

        return result
