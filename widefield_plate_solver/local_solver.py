import subprocess
import os
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS
import logging
import tempfile
from astropy.table import Table

from .exceptions import CouldNotSolveError

logger = logging.getLogger(__name__)


def plate_solve_locally(fits_file_path, sources,
                        ra_approx=None, dec_approx=None,
                        scale_min=None, scale_max=None, use_n_brightest_only=None):
    """
    Calculate the WCS using a local installation of astrometry.net.
    The solve-field binary must be in the path, preferably in /usr/bin.
    You need to have it configured to use the appropriate index files.
    For wide field, a mixture of the 4100 series and 5200 series works well.

    Parameters:
    fits_file_path (Path or str): Path to the FITS file.
    sources (astropy.table.Table): Table of detected sources.
    use_existing_wcs_as_guess (bool): if a wcs information is already present in the fits file, use it to complete
                                      the rest of the arguments of the function. (ra_approx, dec_approx, etc.)
    ra_approx (float): Approximate RA in degrees.
    dec_approx (float): Approximate DEC in degrees.
    scale_min (float): lowest pixel scale to consider in arcsec/pixel
    scale_max (float): largest pixel scale to consider in arcsec/pixel
    use_n_brightest_only (int): number of sources to consider. If None using all.
    redo_if_done (bool): redo even if our solved keyword is already in the header?
    odds_to_solve (float): declare solved beyond those odds

    Returns:
    WCS header if successful, None otherwise.
    Also, updates the given fits file with the same WCS if successful.
    """
    fits_file_path = Path(fits_file_path)
    logger.info(f"plate_solve_locally on {fits_file_path}")

    if use_n_brightest_only is None:
        use_n_brightest_only = len(sources)

    # a work dir for the plate solving arguments
    with tempfile.TemporaryDirectory() as tmpdirname:
        # xylist.fits from sources
        xylist_path = Path(tmpdirname) / 'xylist.fits'
        t = Table([sources['xcentroid'], sources['ycentroid'], sources['flux']],
                  names=('X', 'Y', 'FLUX'))
        t.sort('FLUX', reverse=True)
        t = t[:use_n_brightest_only]
        hdu = fits.BinTableHDU(data=t)
        hdu.writeto(xylist_path, overwrite=True)

        # build solve-field command
        command = ['/usr/bin/solve-field', str(xylist_path), '--no-plots', '--x-column', 'X', '--y-column', 'Y',
                   '--sort-column', 'FLUX']  # by default solve-field sort by largest first, so ok to give flux this way
        # we also need the dimensions of the image:
        header = fits.getheader(fits_file_path)
        command += ['--width', str(header['NAXIS1']), '--height', str(header['NAXIS2'])]
        if ra_approx is not None and dec_approx is not None:
            command += ['--ra', str(ra_approx), '--dec', str(dec_approx), '--radius', '1']
        # add the scale estimate as well
        command += ['--scale-low', str(scale_min), '--scale-high', str(scale_max), '--scale-units', 'arcsecperpix']
        # add the odds
        command += ['--odds-to-solve', str(odds_to_solve)]

        # we'll need this command to use the system python interpreter, not the one running this script.
        # (unless solve-field was installed within this environment ...but likely not the case)
        new_env = os.environ.copy()
        new_env["PATH"] = "/usr/bin:" + new_env["PATH"]  # assuming python is in /usr/bin

        # run command
        try:
            subprocess.run(command, check=True, cwd=tmpdirname, env=new_env)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running solve-field: {e}")
            raise CouldNotSolveError('Error running solve-field.')

        # check for solution and update FITS file
        solved_path = next(Path(tmpdirname).glob('*.wcs'), None)
        if solved_path is None:
            logger.error("Astrometry failed: No solution found.")
            raise CouldNotSolveError('failed to solve astrometry')
        else:
            wcs = WCS(fits.getheader(solved_path)).to_header()
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
