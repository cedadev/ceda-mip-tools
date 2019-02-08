import os
import sys
import requests
import argparse

from ceda_cmip6_tools import config, util, dataset_drs
from ceda_cmip6_tools.permissions_checker import UserPermissionsChecker


"Adds CMIP6 dataset(s) for ingestion to CEDA archive and publication to ESGF."

class CMIP6Adder(object):
    
    def __init__(self,
                 chain=config.chain,
                 configuration=config.configuration,
                 api_url=config.api_url,
                 requester=None):
        self._chain = chain
        self._configuration = configuration
        self._api_url = api_url
        self._requester = requester or util.get_user_name()
        
        self._perms_checker = UserPermissionsChecker(config.ingestion_user)


    def _parse_args(self, arg_list=None):

        "Parses arguments and returns parsed args object."
        parser = argparse.ArgumentParser(description=__doc__)

        parser.add_argument("dirs", nargs="*",
                            metavar="directory", 
                            help=("Dataset directory. "
                                  "Must have format ${BASEDIR}/${DRS_DIRS}/${VERSION_DIR}. "
                                  "Any number of directories may be specified. "
                                  "If none are, then a list is read from standard input "
                                  "(one per line)."))

        args = parser.parse_args(arg_list or sys.argv[1:])

        if not args.dirs:
            args.dirs = [line.strip() for line in sys.stdin]

        return args

    
    def _contains_ncdf_file(self, path):
        for root, dirs, files in os.walk(path):
            for fn in files:
                if fn.endswith('.nc'):
                    return True
        return False

    
    def _validate_dataset_dir(self, path):
        """
        check that the files under the dataset directory are ingestable
        and returns the dataset ID implied by the path
        """

        # check the directory name
        dataset_id = dataset_drs.dir_to_dataset_id(path)
        if dataset_id == None:
            raise Exception("{} does not look like valid DRS path".format(path))


        # check that everything is readable by the ingestion user
        errors = False
        have_ncdf = False

        messages = []

        if not self._perms_checker.check_access(path, 'rx', messages=messages):
            errors = True

        for root, dirs, files in os.walk(path):
            for fn in files:                
                if not self._perms_checker.check_access(os.path.join(root, fn), 
                                            'r', messages=messages):
                    errors = True
                if fn.endswith('.nc'):
                    have_ncdf = True
        
        if not have_ncdf:
            messages.append("{} does not contain any *.nc file".format(path))
            errors = True
            
        if errors:
            raise Exception('\n'.join(['dataset cannot be ingested'] + messages))

        return dataset_id


    def _add_dataset_dir(self, path, dataset_id):
        "adds specified dataset directory to CREPP and parse the response"
        print(self._requester,
              self._chain,
              self._configuration,
              self._api_url,
              path, 
              dataset_id)


    def run(self):
        args = self._parse_args()
        for path in args.dirs:
            print()
            try:
                dataset_id = self._validate_dataset_dir(path)
                self._add_dataset_dir(path, dataset_id)
            except Exception as exc:
                print("ERROR: adding directory {}: {}".format(path, exc))
                continue
            print("INFO: added directory {}\n(dataset id = {}".format(path, dataset_id))
        print()

def main():
    c6a = CMIP6Adder()
    c6a.run()
    