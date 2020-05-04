from os import path, walk, makedirs
from tqdm import tqdm
from sys import exit, stderr
import numpy as np
import gdal
import cv2

def gdalWrite(fn, img, geo_transform):
    if len(img.shape) > 2:
        width = img.shape[2]
        height = img.shape[1]
        chanel = img.shape[0]
    else:
        width = img.shape[1]
        height = img.shape[0]
        chanel = 1
    target_x = gdal.GetDriverByName('GTiff').Create(fn, width, height, chanel,
                                                    gdal.GDT_Byte, options=['COMPRESS=LZW'])
    target_x.WriteRaster(0, 0, width, height, img.tostring())
    if geo_transform:
        target_x.SetGeoTransform(geo_transform)
    target_x.FlushCache()
    target_x = None


def make_data(image_dir, label_dir, oimage_dir, olabel_dir):
    # Getting all files in the directory provided for jsons
    labels = [j for j in next(walk(label_dir))[2] if '_post' in j]
    fnum = len(labels)
    for post in tqdm(labels):
        pre = post.replace('_post', '_pre')
        fpre = path.join(image_dir, pre)
        fpost = path.join(image_dir, post)
        flabel = path.join(label_dir, post)
        fo = post.replace('_post_disaster.png', '.tif')
        fimgo = path.join(oimage_dir, fo)
        flabo = path.join(olabel_dir, fo)
        # copy label
        lab = cv2.imread(flabel, cv2.IMREAD_GRAYSCALE)
        gdalWrite(flabo, lab, None)
        img_pre = cv2.imread(fpre, cv2.IMREAD_COLOR)
        img_post = cv2.imread(fpost, cv2.IMREAD_COLOR)
        img = np.concatenate((img_pre, img_post), axis=-1)
        img = np.transpose(img, [2, 0, 1])
        gdalWrite(fimgo, img, None)
        en = 1


if __name__ == "__main__":
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description=
        """mask_polygons.py: Takes in xBD dataset and masks polygons in the image\n\n
        WARNING: This could lead to hundreds of output images per input\n""")

    parser.add_argument('--input',
                        required=True,
                        metavar="/path/to/xBD/",
                        help='Path to parent dataset directory "xBD"')
    parser.add_argument('--output',
                        required=True,
                        metavar="/path/to/xBD_change/",
                        help='Path to parent dataset directory "xBD"')
    args = parser.parse_args()
    input = args.input
    output = args.output

    # Getting the list of the disaster types under the xBD directory
    disasters = next(walk(args.input))[1]

    # make output dirs
    oimage_dir = path.join(output, 'images')
    olabel_dir = path.join(output, 'labels')
    for cdir in (output, oimage_dir, olabel_dir):
        if not path.isdir(cdir):
            makedirs(cdir)

    for disaster in tqdm(disasters, desc='Masking', unit='disaster'):
        # Create the full path to the images, labels, and mask output directories
        image_dir = path.join(args.input, disaster, 'images')
        label_dir = path.join(args.input, disaster, 'masks')

        if not path.isdir(image_dir):
            print(
                "Error, could not find image files in {}.\n\n"
                .format(image_dir),
                file=stderr)
            exit(2)

        if not path.isdir(label_dir):
            print(
                "Error, could not find label files in {}.\n\n"
                .format(label_dir),
                file=stderr)
            exit(2)

        make_data(image_dir, label_dir, oimage_dir, olabel_dir)