from setuptools import setup, find_packages

setup(
    name='widefield_plate_solver',
    version='0.1.1',
    author='Frédéric Dux',
    author_email='duxfrederic@gmail.com',
    packages=find_packages(),
    scripts=['widefield_plate_solver/script.py'],
    entry_points={
        'console_scripts': [
            'widefield-plate-solve=widefield_plate_solver.script:main',
        ],
    },
    url='http://pypi.python.org/pypi/widefield_plate_solver/',
    license='LICENSE.txt',
    description='An astronomical image plate solving package.',
    long_description=open('README.md').read(),
    install_requires=[
        'scipy',
        'astropy',
        'sep',
        'matplotlib',
        'astroquery',
        'requests'
    ],
)
