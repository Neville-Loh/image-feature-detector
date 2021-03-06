import sys
import argparse
import os
from matplotlib import pyplot

import solem.distancedistributions
from data_exploration.image_plot import plot_side_by_side_pairs
from data_exploration.util import reject_outliers
import imageIO.readwrite as IORW
import imageProcessing.pixelops as IPPixelOps
import imageProcessing.smoothing as IPSmooth
from image_stiching.feature_descriptor.feature_descriptor import match_corner_by_ncc, reject_outlier_pairs
from image_stiching.harris_conrner_detection.harris import compute_harris_corner
from image_stiching.homography.homography import fit_transform_homography
from image_stiching.performance_evaulation.timer import measure_elapsed_time
from image_stiching.stiching import stitch
from image_stiching.util.save_object import save_object_at_location, load_object_at_location

CHECKER_BOARD = "./images/cornerTest/checkerboard.png"
MOUNTAIN_LEFT = "./images/panoramaStitching/tongariro_left_01.png"
MOUNTAIN_RIGHT = "./images/panoramaStitching/tongariro_right_01.png"
MOUNTAIN_SMALL_TEST = "./images/panoramaStitching/tongariro_left_01_small.png"
SNOW_LEFT = "./images/panoramaStitching/snow_park_left_berg_loh_02.png"
SNOW_RIGHT = "./images/panoramaStitching/snow_park_right_berg_loh_02.png"
OXFORD_LEFT = "./images/panoramaStitching/oxford_left_berg_loh_01.png"
OXFORD_RIGHT = "./images/panoramaStitching/oxford_right_berg_loh_01.png"


def prepareRGBImageFromIndividualArrays(r_pixel_array, g_pixel_array, b_pixel_array, image_width, image_height):
    rgbImage = []
    for y in range(image_height):
        row = []
        for x in range(image_width):
            triple = []
            triple.append(r_pixel_array[y][x])
            triple.append(g_pixel_array[y][x])
            triple.append(b_pixel_array[y][x])
            row.append(triple)
        rgbImage.append(row)
    return rgbImage


def pixelArrayToSingleList(pixelArray):
    list_of_pixel_values = []
    for row in pixelArray:
        for item in row:
            list_of_pixel_values.append(item)
    return list_of_pixel_values


@measure_elapsed_time
def filenameToSmoothedAndScaledpxArray(filename):
    (image_width, image_height, px_array_original) = IORW.readRGBImageAndConvertToGreyscalePixelArray(filename)
    px_array_smoothed = IPSmooth.computeGaussianAveraging3x3(px_array_original, image_width, image_height)

    # make sure greyscale image is stretched to full 8 bit intensity range of 0 to 255
    px_array_smoothed_scaled = IPPixelOps.scaleTo0And255AndQuantize(px_array_smoothed, image_width, image_height)
    return px_array_smoothed_scaled


def basic_comparison(histogram=False):
    try:
        pairs = load_object_at_location(os.path.join(".", "cache", "default_pairs_cache.pkl"))
    except FileNotFoundError:
        left_px_array = filenameToSmoothedAndScaledpxArray(MOUNTAIN_LEFT)
        right_px_array = filenameToSmoothedAndScaledpxArray(MOUNTAIN_RIGHT)

        height, width = len(left_px_array), len(left_px_array[0])

        left_corners = compute_harris_corner(left_px_array,
                                             n_corner=1000,
                                             alpha=0.04,
                                             gaussian_window_size=7,
                                             plot_image=False)

        right_corners = compute_harris_corner(right_px_array,
                                              n_corner=1000,
                                              alpha=0.04,
                                              gaussian_window_size=7,
                                              plot_image=False)

        # get the best matches for each corner in the left image
        pairs = match_corner_by_ncc((left_px_array, left_corners),
                                    (right_px_array, right_corners),
                                    feature_descriptor_patch_size=15,
                                    threshold=0.9)
        save_object_at_location(
            os.path.join(".", "cache", "default_pairs_cache.pkl"),
            pairs)

    # get the homography matrix
    result_image = fit_transform_homography(pairs,
                                            source_left_image_path=MOUNTAIN_LEFT,
                                            source_right_image_path=MOUNTAIN_RIGHT)
    pyplot.imshow(result_image)
    print(f'[INFO] Showing the result image...')
    pyplot.show()

def main():
    # Retrieve all command line argument
    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]

    # If there is no argument, compute a basic comparison with default image
    if len(args) == 0 and len(opts) == 0:
        basic_comparison()

    # Parse all additional argument if there is any
    else:
        parser = argparse.ArgumentParser(description='A basic image stitching program written by Neville Loh and '
                                                     'Nicholas Berg.')

        # input image path parameters
        parser.add_argument('input1', metavar='input', type=str, help='The left image to be stitched.')

        # Input File
        parser.add_argument('input2', metavar='input2', type=str, help='The right image to be stitched.')

        # Corner number argument Optional
        parser.add_argument('-n', '--n_corner',
                            type=int,
                            help='Number of corner output by the algorithm. The output image will contain n corners '
                                 'with the strongest response. If nothing is supplied, default to 1000',
                            default=1000)

        # Gaussian windows size argument Optional
        parser.add_argument('-a', '--alpha',
                            type=float,
                            help='The Harris Response constant alpha. Specifies the weighting between corner with '
                                 'strong with single direction and multi-direction. A higher alpha will result in '
                                 'less difference between response of ingle direction and multi-direction shift in '
                                 'intensity. If nothing is supplied, default to 0.04'
                            , default=0.04)

        # Gaussian windows size argument, int Optional
        parser.add_argument('-w', '--winsize',
                            type=int,
                            help='Gaussian windows size which applied the the squared and mix derivative of the image.'
                                 'A higher windows size will result in higher degree of smoothing, If nothing is '
                                 'supplied, the default widows size is set to 5.',
                            default=5)

        # Plot harris corner argument Optional
        parser.add_argument('-ph', '--plot_harris_corner',
                            type=bool,
                            help='Plot the Harris corner response. If nothing is supplied, the default is set to False',
                            default=False)

        # Feature Descriptor Path Size, int Optional
        parser.add_argument('-fds', '--feature_descriptor_patch_size',
                            type=int,
                            help='The size of the feature descriptor patch. If nothing is supplied, the default '
                                 'patch size is set to 15.',
                            default=15)

        # Feature Descriptor Threshold, float Optional
        parser.add_argument('-fdt', '--feature_descriptor_threshold',
                            type=float,
                            help='The threshold of the feature descriptor. If nothing is supplied, the default '
                                 'threshold is set to 0.9',
                            default=0.9)

        # Outlier Rejection, bool Optional
        parser.add_argument('-or', '--enable_outlier_rejection',
                            type=bool,
                            help='Enable outlier rejection. If nothing is supplied, the default is set to True',
                            default=True)

        # Outlier Rejection M, float Optional
        parser.add_argument('-orm', '--outlier_rejection_std',
                            type=float,
                            help='The outlier rejection standard deviation to include. If nothing is supplied, '
                                 'the default is set to 1',
                            default=1)



        args = vars(parser.parse_args())

        # Compute and plot Harris Corner with optional or default values
        img = filenameToSmoothedAndScaledpxArray(args['input1'])
        img2 = filenameToSmoothedAndScaledpxArray(args['input2'])
        stitch(
            left_px_array=img,
            right_px_array=img2,
            n_corner=args['n_corner'],
            alpha=args['alpha'],
            gaussian_window_size=args['winsize'],
            plot_harris_corner=args['plot_harris_corner'],
            feature_descriptor_patch_size=args['feature_descriptor_patch_size'],
            feature_descriptor_threshold=args['feature_descriptor_threshold'],
            enable_outlier_rejection=args['enable_outlier_rejection'],
            outlier_rejection_m=args['outlier_rejection_std'],
            plot_result=True,
            left_source_path=args['input1'],
            right_source_path=args['input2'],
        )


if __name__ == "__main__":
    main()
