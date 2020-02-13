from distutils.core import setup
import setuptools
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict

dependencies = [
    'gdal>=2.2.0',
    'lxml>=3.5.0',
    'numpy>=1.11.0',
    'scipy>=0.17.0',
    'matplotlib>=1.5.1',
]

pkg_resources.require(dependencies)

setup(name='s2snow',
      version='1.6',
      description='Supplementary python scripts for OTB remote module: let-it-show (LIS)',
      url='https://gitlab.orfeo-toolbox.org/remote_modules/let-it-snow',
      author='CNES',
      author_email='otb@cnes.fr',
      license='GNU Affero General Public License v3.0',
      packages=['s2snow'],
      #setup_requires=dependencies,
      scripts=['scripts/run_cloud_removal.py',
               'scripts/run_snow_annual_map.py',
               'scripts/run_snow_detector.py',
               'scripts/build_json.py'
      ],
      # entry_points={
      #     'console_scripts': [
      #         'lis_run_cloud_removal=run_cloud_removal:main',
      #         'lis_run_snow_annual_map=run_snow_annual_map:main',
      #         'lis_run_snow_detector=run_snow_detector:main',
      #         'lis_build_json=build_json:main'
      #     ],
      # },
)
