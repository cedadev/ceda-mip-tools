__copyright__ = "Copyright 2018 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENCE file in top-level package directory"

from setuptools import setup, find_packages

from ceda_mip_tools import __version__ as _package_version

setup(
    name='ceda_mip_tools',
    version=_package_version,
    description='CEDA MIP tools',
    url='https://github.com/cedadev/ceda_mip_tools/',
    license='BSD - See ceda_mip_tools/LICENCE file for details',
    packages=find_packages(),
    package_data={
        'ceda_mip_tools': [
            'LICENCE',
        ],
    },
    install_requires=['requests'],
    
    # This qualifier can be used to selectively exclude Python versions - 
    # in this case early Python 2 and 3 releases
    python_requires='>=3.5.0', 
    
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'add-to-mip = ceda_mip_tools.add_mip_dataset:main',
            'mip-dataset-status = ceda_mip_tools.mip_dataset_status:main'
            ],
        }
)
