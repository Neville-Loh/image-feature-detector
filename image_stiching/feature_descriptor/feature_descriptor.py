from typing import List, Type, Tuple, Union
import numpy as np
from image_stiching.corner import Corner
from image_stiching.harris_conrner_detection.harris_util import compute_gaussian_averaging

"""
Feature Descriptor
"""


def get_patches(corners: List[Type[Corner]], patch_size: int, img: np.ndarray) -> \
        List[Type[Corner]]:
    """
    Get the patches from the image

    Parameters
    ----------
    corners : List[Type[Corner]]
        List of corners
    patch_size : int
        Size of the patch
    img : np.ndarray
        Image

    Returns
    -------
        List[Type[Corner]]
    """
    center_index = patch_size // 2

    img = np.array(img)
    img = compute_gaussian_averaging(img, windows_size=7)

    result_corners = []
    length, width = img.shape
    print(img[0][:].shape)
    print(f'image shpae = {img.shape}')
    for c in corners:
        # ignore border
        if c.x < center_index or c.x > width - center_index \
                or c.y < center_index or c.y > length - center_index:
            print(c.x, c.y)
        else:
            # print(type(c.x- center_index))
            # getting the window
            patch: np.ndarray = img[c.y - center_index: c.y + center_index + 1,
                                     c.x - center_index: c.x + center_index + 1]

            patch = (patch - np.mean(patch))

            # setting the result
            c.feature_descriptor = patch

            if patch.shape != (15, 15):
                print(f'x = {c.x},y={c.y}, shape={patch.shape}')
            else:
                result_corners.append(c)
            # c.feature_descriptor = patch.flatten()

    return result_corners


def compute_NCC(patch1: np.ndarray, patch2: np.ndarray) -> float:
    """
    Compute the normalised cross correlation between two patches

    parameters
    ----------
    patch1 : np.ndarray
        First patch
    patch2 : np.ndarray
        Second patch

    Returns
    -------
        float
    """
    # compute the normalised cross correlation
    return np.sum(patch1 * patch2) / (np.sqrt(np.sum(patch1 ** 2)) * np.sqrt(np.sum(patch2 ** 2)))


def compare(corners1: List[Type[Corner]], corners2: List[Type[Corner]]) -> List[
    Tuple[Type[Corner], Type[Corner], float]]:
    """
    compare the two list of corners

    Parameters
    ----------
    corners1 : List[Type[Corner]]
        List of corners
    corners2 : List[Type[Corner]]
        List of corners

    Returns
    -------
        List[Type[Corner]]
    """
    pairs = []
    for c1 in corners1:
        # initialize the best match
        first_corner = corners2[0]
        ncc = compute_NCC(c1.feature_descriptor, first_corner.feature_descriptor)
        best = (first_corner, ncc)
        best2 = (first_corner, ncc)
        for c2 in corners2[1:]:
            result = compute_NCC(c1.feature_descriptor, c2.feature_descriptor)

            # check if result greater than 2nd best, if yes, replace 2nd best
            if result > best[1]:
                best2 = best
                best = (c2, result)
            # compare the with the second best value
            elif result > best2[1]:
                best2 = (c2, result)

        # check ratio between 2nd best match and best
        ratio = best2[1] / best[1]
        if ratio <= 0.9:
            pairs.append((c1, best[0], best[1]))

    return pairs