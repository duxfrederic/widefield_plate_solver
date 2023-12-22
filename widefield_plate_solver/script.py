#!/usr/bin/env python
import argparse
from pathlib import Path
from widefield_plate_solver import plate_solve
from widefield_plate_solver.plotter import plot_stars_with_wcs


def main():
    parser = argparse.ArgumentParser(description="Plate solve astronomical images. We will extract the sources.")
    parser.add_argument("fits_file_path", help="Path to the FITS file to add astrometry to.")
    parser.add_argument("--do_not_guess_from_header", action="store_false", help="No guess from the fits header.")
    parser.add_argument("--use_api", action="store_true", help="Use API for plate solving. Else use local installation.")
    parser.add_argument("--redo", action="store_true", help="Redo plate solving even if already done")
    parser.add_argument("--verbose", action="store_true", help="Print the WCS if success.")
    parser.add_argument("--plot", action="store_true", help="Plot the field with coordinate grid overlayed if success.")
    parser.add_argument("--ra_approx", type=float, help="Approximate RA in degrees.")
    parser.add_argument("--dec_approx", type=float, help="Approximate DEC in degrees.")
    parser.add_argument("--scale_min", type=float, help="Lowest pixel scale to consider in arcsec/pixel.")
    parser.add_argument("--scale_max", type=float, help="Largest pixel scale to consider in arcsec/pixel.")
    parser.add_argument("--use_n_brightest_only", type=int, help="Default 15. Number of sources to use, Brightest first.")

    args = parser.parse_args()

    if args.ra_approx is not None or args.dec_approx is not None or args.scale_min is not None or args.scale_max is not None:
        use_existing_wcs_as_guess = False
    else:
        use_existing_wcs_as_guess = args.do_not_guess_from_header

    use_n_brightest_only = 15 if args.use_n_brightest_only is None else args.use_n_brightest_only

    wcs_header = plate_solve(args.fits_file_path, sources=None, use_api=args.use_api, redo_if_done=args.redo,
                             use_existing_wcs_as_guess=use_existing_wcs_as_guess,
                             ra_approx=args.ra_approx, dec_approx=args.dec_approx,
                             scale_min=args.scale_min, scale_max=args.scale_max,
                             use_n_brightest_only=use_n_brightest_only, do_debug_plot=args.plot)

    if len(wcs_header) == 0:
        print(f"Failed to solve field: {args.fits_file_path}")
        return

    if len(wcs_header) > 0 and args.plot:
        savepath = Path(args.fits_file_path).with_suffix('.jpeg')
        plot_stars_with_wcs(args.fits_file_path, savepath=savepath)

    if args.verbose:
        print("Plate solving completed. WCS Header:")
        print(wcs_header)


if __name__ == "__main__":
    main()
