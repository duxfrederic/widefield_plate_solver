from astropy.io import fits
from astropy.wcs import WCS
import logging
from pathlib import Path

from .local_solver import plate_solve_locally
from .api_solver import plate_solve_with_API
from .extract_stars import extract_stars


def plate_solve(fits_file_path, sources=None, use_existing_wcs_as_guess=True,
                use_n_brightest_only=None, redo_if_done=False, use_api=True,
                ra_approx=None, dec_approx=None, scale_min=None, scale_max=None,
                logger=None, do_debug_plot=False, odds_to_solve=None):
    """
    Super function to decide between local and API plate solving.

    Parameters:
    fits_file_path (Path or str): Path to the FITS file.
    sources (astropy.table.Table): Table of detected sources. If None, runs the source extractor in extract_stars.py
    use_existing_wcs_as_guess (bool): If True, use existing WCS info as a guess.
    use_n_brightest_only (int): Number of sources to consider. If None, use all.
    redo_if_done (bool): Redo even if our solved keyword is already in the header?
    use_api (bool): If True, use the API for plate solving, otherwise use local.
    ra_approx (float): Approximate RA in degrees.
    dec_approx (float): Approximate DEC in degrees.
    scale_min (float): lowest pixel scale to consider in arcsec/pixel
    scale_max (float): largest pixel scale to consider in arcsec/pixel
    logger (logging.logger): if you feel fancy, provide a logger.
    do_debug_plot (bool): will dump an image of the extracted sources.
    odds_to_solve: odds to declare solved. we can lower it for small fields when we specify a search radius.

    Returns:
    WCS header if successful, None otherwise.
    """

    # default logger if none provided
    if logger is None:
        logger = logging.getLogger(__name__)
        if not logger.hasHandlers():
            # Configure logging to print to the standard output
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    # check, maybe we already solved it
    header = fits.getheader(fits_file_path)
    if not redo_if_done and 'PL-SLVED' in header:
        logger.info(f"{fits_file_path} was already plate solved, no redoing.")
        # we already treated it.
        # the header contains the WCS info.
        return header

    if sources is None:
        if do_debug_plot:
            sourceplotpath = Path(fits_file_path).parent / f"{Path(fits_file_path).stem}_sources.jpeg"
        else:
            sourceplotpath = None

        sources = extract_stars(fits_file_path, debug_plot_path=sourceplotpath)

    if use_existing_wcs_as_guess:
        with fits.open(fits_file_path) as hdul:
            header = hdul[0].header
            wcs_info = WCS(header)
            if wcs_info.is_celestial:
                ra_approx, dec_approx = wcs_info.wcs.crval
                # in arcsec/pixel:
                scale = 3600*(wcs_info.pixel_scale_matrix[0, 0]**2 + wcs_info.pixel_scale_matrix[0, 1]**2)**0.5
                scale_min, scale_max = 0.8 * scale, 1.2 * scale

    if use_api:
        if odds_to_solve is not None:
            logger.info('Parameter ignored: odds_to_solve not available with API solving')
        return plate_solve_with_API(fits_file_path, sources, ra_approx=ra_approx, dec_approx=dec_approx,
                                    scale_min=scale_min, scale_max=scale_max, use_n_brightest_only=use_n_brightest_only)
    else:
        if odds_to_solve is None:
            odds_to_solve = 1e6
        return plate_solve_locally(fits_file_path, sources, ra_approx=ra_approx, dec_approx=dec_approx,
                                   scale_min=scale_min, scale_max=scale_max, use_n_brightest_only=use_n_brightest_only,
                                   odds_to_solve=odds_to_solve)
