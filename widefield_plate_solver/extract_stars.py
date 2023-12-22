import numpy as np
from scipy.ndimage import median_filter
from astropy.io import fits
from astropy.table import Table
import sep
import pathlib

from .plotter import plot_stars


def extract_stars(fits_file_path_or_2darray, debug_plot_path=None):
    """
    Extract star positions from an image using SEP (Source Extractor as a Python library).

    Parameters:
    fits_file_path (str): Path to the FITS file.
    debug_plot (str): if provided, dumps a jpeg showing the extracted sources at the given path.

    Returns:
    astropy.table.Table: Table of detected sources.
    numpy 2D array: background subtracted image
    """
    if type(fits_file_path_or_2darray) is str or type(fits_file_path_or_2darray) is pathlib.PosixPath:
        image = fits.getdata(fits_file_path_or_2darray).astype(float)
    else:
        image = fits_file_path_or_2darray

    bkg = sep.Background(image, bw=64, bh=64, fw=3, fh=3)
    image_filtered = median_filter(image, size=2)

    image_sub = image_filtered - bkg
    objects = sep.extract(image_sub, thresh=4, err=bkg.globalrms,
                          minarea=10)

    sources = Table()
    for col in objects.dtype.names:
        sources[col] = objects[col]

    # just to stick to the daostarfinder way
    sources['xcentroid'] = sources['x']
    sources['ycentroid'] = sources['y']

    # remove flagged
    sources = sources[sources['flag'] == 0]

    # remove the weirdly elongated ones
    elongation = sources['a'] / sources['b']
    med_el = np.median(elongation)
    std_el = np.std(elongation)
    sources['elongation'] = elongation
    sources = sources[sources['elongation'] < med_el + std_el]

    # remove those occupying a weirdly small amount of space (likely hot pixels or cosmics)
    medpix = np.median(sources['npix'])
    sources = sources[(sources['npix'] > 0.5 * medpix)]

    # brightest first
    sources.sort('flux', reverse=True)

    if debug_plot_path is not None:
        plot_stars(sources, image_sub, debug_plot_path)

    return sources
