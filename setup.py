__copyright__ = "Copyright 2018 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENCE file in top-level package directory"

from setuptools import setup, find_packages

from ceda_cmip6_tools import __version__ as _package_version

setup(
    name='ceda_cmip6_tools',
    version=_package_version,
    description='CEDA CMIP6 tools',
    url='https://github.com/cedadev/ceda_cmip6_tools/',
    license='BSD - See ceda_cmip6_tools/LICENCE file for details',
    packages=find_packages(),
    package_data={
        'ceda_cmip6_tools': [
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
            'add-to-cmip6 = ceda_cmip6_tools.add_to_cmip6:main',
            'cmip6-dataset-status = ceda_cmip6_tools.cmip6_dataset_status:main',
            'init-cmip6-migrations = ceda_cmip6_tools.init_cmip6_migrations:main',
            'request-cmip6-migration = ceda_cmip6_tools.request_cmip6_migration:main',
            'request-cmip6-retrieval = ceda_cmip6_tools.request_cmip6_retrieval:main',
            'list-cmip6-requests = ceda_cmip6_tools.list_cmip6_requests:main',
            'withdraw-cmip6-migration-request = ceda_cmip6_tools.withdraw_cmip6_migration_request:main',
            'withdraw-cmip6-retrieval-request = ceda_cmip6_tools.withdraw_cmip6_retrieval_request:main',
            ],
        }
)



