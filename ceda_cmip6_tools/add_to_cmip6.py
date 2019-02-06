import os
import sys
import requests
import argparse
import pwd

import ceda_cmip6_tools.config as config


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
        self._requester = requester or self._get_user_name()


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

    
    def _get_user_name(self):
        "get a user name (to use as the requester)"
        name = pwd.getpwuid(os.getuid()).pw_gecos
        return name[: config.max_requester_len]


    def _validate_dataset_dir(self, path):
        """
        check that the files under the dataset directory are ingestable
        and returns the dataset ID implied by the path
        """
        return "test"


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
            dataset_id = self._validate_dataset_dir(path)
            self._add_dataset_dir(path, dataset_id)
        

def main():
    c6a = CMIP6Adder()
    c6a.run()
    
