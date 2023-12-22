#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  9 08:04:20 2023

@author: fred
"""

from astropy.io import fits
import requests
import json
import os
from astroquery.astrometry_net import AstrometryNet
import logging

from .exceptions import CouldNotSolveError, APIKeyNotFound

logger = logging.getLogger(__name__)


def plate_solve_with_API(fits_file_path, sources,
                         ra_approx=None, dec_approx=None,
                         scale_min=None, scale_max=None, use_n_brightest_only=None):
    """
    Calculate the WCS using the nova.astrometry.net API.
    In this case, we first extract the sources and only send those over
    the internet.
    We get back an astrometric solution contained in a fits file.

    Parameters:
    fits_file_path (str): Path to the FITS file.
    sources (astropy.table.Table): Table of detected sources.
    ra_approx: float in degrees, approximate center of the field coord
    dec_approx: float in degrees, approximate center of the field coord
    scale_min (float): lowest pixel scale to consider in arcsec/pixel
    scale_max (float): largest pixel scale to consider in arcsec/pixel
    use_n_brightest_only (int): number of sources to consider. If None using all.
    redo_if_done (bool): redo even if our solved keyword is already in the header?

    Returns:
    WCS header if successful, None otherwise.

    """
    # check api key
    if 'astrometry_net_api_key' not in os.environ:
        raise APIKeyNotFound

    if use_n_brightest_only is None:
        use_n_brightest_only = len(sources)

    logger.info(f"plate_solve_with_API on {fits_file_path}")

    # unpack the positions
    tupledetections = [(star['xcentroid'], star['ycentroid']) for star in sources[:use_n_brightest_only]]
    x, y = list(zip(*tupledetections))

    # create a session
    R = requests.post('http://nova.astrometry.net/api/login',
                      data={'request-json': json.dumps({"apikey": os.environ['astrometry_net_api_key']})})

    ast = AstrometryNet()
    ast._session_id = R.json()['session']

    # the dimensions of the image...
    header = fits.getheader(fits_file_path)
    nx, ny = header['NAXIS1'], header['NAXIS2']

    # can we make the solver find the solution faster?
    # let's give it an approximate pointing.
    morekwargs = {}
    if ra_approx is not None and dec_approx is not None:
        morekwargs['center_ra'] = ra_approx
        morekwargs['center_dec'] = dec_approx
        morekwargs['radius'] = 2.
    try:
        scale_est = 0.5 * (scale_max + scale_min)
        scale_err = 100 * abs(scale_max - scale_min) / scale_est  # in %
        wcs = ast.solve_from_source_list(x, y, nx, ny,
                                         scale_est=scale_est,
                                         scale_err=scale_err,
                                         scale_units='arcsecperpix',
                                         publicly_visible='n',
                                         **morekwargs)
    except Exception as e:
        # anything ...
        logger.info(f"plate_solve_with_API: something went wrong ({e}) with API when trying to solve {fits_file_path}")
        raise

    # it can also have actually failed.
    # happens if the selected stars are too faint, or if our sources
    # contain too many artifacts.
    # or if we don't have enough stars
    # or ...many other reasons.
    if len(wcs) == 0:
        logger.info(f"plate_solve_with_API: could not plate solve {fits_file_path}")

        raise CouldNotSolveError('Astrometry.net failed! WCS empty. Try with different stars or a different image?')

    # else, we're probably fine. Like, 99.9% confidence from my
    # experience with astrometry.net's plate solver.
    logger.info(f"plate_solve_with_API: {fits_file_path} solved, writing the WCS")
    with fits.open(fits_file_path, mode="update") as hdul:
        # little flag to indicate that we plate solved this file:
        wcs['PL-SLVED'] = 'done'
        # add all this info to the file:
        hdul[0].header.update(wcs)
        hdul.flush()
    return wcs





