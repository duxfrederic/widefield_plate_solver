# Widefield Plate Solver

This package provides tools for plate solving wide field astronomical images.
Its main difference with using Astrometry.net's `solve-field` directly is that it can also default to Astrometry.net's API if requested. 


## Installation

To install the package, run:
```bash
$ pip install widefield-plate-solver
```

## Usage

### as a script

After installation, you can use the command `widefield-plate-solve` from the terminal:

```bash
$ widefield-plate-solve <fits_file_path> --use_api
```
Replace `<fits_file_path>` with the path to your FITS file. 
Use the `--use_api` flag to use the Astrometry.net API for plate solving: your environment variables will need to contain your API key.

```bash
$ export astrometry_net_api_key="your_nova_astrometry_api_key" 
```
Not using `--use_api` will default to your local installation of Astrometry.net, looking for the `solve-field` command. 

For more information on usage, run:

```bash
$ widefield-plate-solve --help
```

### from python

See the `plate_solve` function imported from the package:

```python
from widefield_plate_solver import plate_solve
help(plate_solve)
```

## Dependencies

- scipy
- astropy
- sep
- matplotlib
- astroquery
