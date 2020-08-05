import os, subprocess


def create_textures(HSIZE,WSIZE):

    HSIZE = HSIZE
    WSIZE = WSIZE
    #KERNEL_SIZES = [3, 5, 7, 9, 11, 13, 15, 17]
    KERNEL_SIZES = [3]
    INPUT_DIR = '/Users/adambradley/Python_Dev/InLineViz/img_patches/inputs'
    OUTPUT_DIR = '/Users/adambradley/Python_Dev/InLineViz/img_patches/outputs'

    for filename in os.listdir(INPUT_DIR):
      basename, ext = os.path.splitext(filename)
      input_file = os.path.join(INPUT_DIR, filename)
      for k in KERNEL_SIZES:
        output_file = '%s_%d_k%d%s' % (basename, HSIZE, k, ext)
        output_file = os.path.join(OUTPUT_DIR, output_file)
        cmd = ('th synthesis.lua -source %s -output_file %s '
               '-height %d -width %d -k %d') % (
                   input_file,
                   output_file,
                   HSIZE,
                   WSIZE,
                   k)
        print(cmd)
        subprocess.call(cmd, shell=True)
