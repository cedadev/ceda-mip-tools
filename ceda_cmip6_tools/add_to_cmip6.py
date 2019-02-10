"""
Adds CMIP6 dataset(s) for ingestion to CEDA archive and publication to ESGF.
"""

import os
import sys
import requests
import argparse

from ceda_cmip6_tools import config, util, dataset_drs
from ceda_cmip6_tools.permissions_checker import UserPermissionsChecker


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
        permissions = []
        checker_args = {
            'messages': messages,
            'permissions': permissions,
            'continue_on_error': True 
            }

        if not self._perms_checker.check_access(path, 'rx', **checker_args):
            errors = True

        for root, dirs, files in os.walk(path):
            for fn in files:
                file_path = os.path.join(root, fn)
                if fn.endswith('.nc'):
                    have_ncdf = True
                    if not self._perms_checker.check_access(file_path, 
                                                            'r', **checker_args):
                        errors = True
                else:
                    messages.append('invalid filename (not *.nc):\n   {}'.format(file_path))
                    errors = True
                    
            # also check (non-recursively) that directories are readable
            # (if they contain any files then execute permission will get checked
            # as part of checking the files)
            for dn in dirs:
                dir_path = os.path.join(root, dn)
                if not self._perms_checker.check_access(dir_path, 
                                                        'r',
                                                        **checker_args):
                    errors = True

        if not have_ncdf:
            messages.append("does not contain any valid files")
            errors = True
            
        if errors:
            message = '\n'.join(['dataset cannot be ingested'] + messages)

            for path, stat_data in permissions:
                if stat_data.st_uid == 0:
                    drawline = "=" * 80 + "\n"
                    message += ("\n{}Please email support@ceda.ac.uk "
                                "to ask for user '{}' to be given access to\n"
                                "{}\n{}").format(drawline, config.ingestion_user,
                                                 path, drawline)

            raise Exception(message)

        return dataset_id


    def _add_dataset_dir(self, path, dataset_id):
        "adds specified dataset directory to CREPP and parse the response"
       
        url = self._api_url

        params = {'chain': self._chain,
                  'config': self._configuration,
                  'dataset_id': dataset_id,
                  'directory': path,
                  'requester': self._requester}
        
        response = requests.post(url, data=params)

        if response.status_code != 200:
            print(response.status_code)
            raise Exception("Could not talk to data publication system")
        
        try:
            fields = response.json()
            status = fields['status']
        except (ValueError, KeyError):
            raise Exception("Could not parse response from CMIP6 publication system")
        
        if status != 0:
            message = 'CMIP6 publication system did not accept dataset'
            try:
                message += ': ' + fields['message']
            except KeyError:
                pass
            raise Exception(message)


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
    
