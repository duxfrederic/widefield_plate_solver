from astropy.io import fits
from astropy.wcs import WCS
import matplotlib.pyplot as plt
from astropy.visualization import ZScaleInterval


def plot_stars_with_wcs(fits_file_path, sources=None, savepath=None):
    """
    Plot the updated image with WCS projection and marked detected sources.
    This is to be used for diagnostics.

    Parameters:
    fits_file_path (str): Path to the updated FITS file with WCS.
    sources (astropy.table.Table): Table of detected sources.
    """
    with fits.open(fits_file_path) as hdul:
        wcs = WCS(hdul[0].header)
        image = hdul[0].data

    fig = plt.figure(figsize=(15, 15))
    ax = plt.subplot(projection=wcs)
    interval = ZScaleInterval(contrast=0.1)
    vmin, vmax = interval.get_limits(image)

    ax.imshow(image, cmap='gray', origin='lower', vmin=vmin, vmax=vmax)
    ax.grid(color='white', ls='solid')
    ax.set_xlabel('Right Ascension')
    ax.set_ylabel('Declination')

    if sources is not None:
        ra, dec = wcs.all_pix2world(sources['xcentroid'], sources['ycentroid'], 0)
        ax.plot(ra, dec, 'o', color='red', label='Detected Sources', mfc='None',
                transform=ax.get_transform('world'))

    plt.legend()
    if savepath is None:
        plt.show()
    else:
        plt.savefig(savepath)


def plot_stars(sources, image, savepath=None):
    """
    Plot the image with detected sources marked (for debugging).

    Parameters:
    sources (astropy.table.Table): Table of detected sources.
    image (numpy.ndarray): Image data.
    """
    plt.figure(figsize=(15, 15))
    interval = ZScaleInterval(contrast=0.1)
    vmin, vmax = interval.get_limits(image)
    plt.imshow(image, cmap='gray', origin='lower', vmin=vmin, vmax=vmax)
    plt.colorbar()
    plt.plot(sources['xcentroid'], sources['ycentroid'], 'o',
             color='red', label='Detected Sources', alpha=0.5,
             ms=10,
             mfc='None')
    plt.legend()
    plt.tight_layout()
    if savepath is None:
        plt.show()
    else:
        plt.savefig(savepath)