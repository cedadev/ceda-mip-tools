"""
Adds MIP dataset(s) for ingestion to CEDA archive and publication to ESGF.
"""

import os
import sys

from ceda_mip_tools.pub_sys_intfc import config, util
from ceda_mip_tools.pub_sys_intfc.permissions_checker import UserPermissionsChecker


class MIPAdder(object):

    def __init__(self,
                 configuration=config.configuration,
                 api_url_root=config.api_url_root,
                 requester=None):
        self._configuration = configuration
        self._api_add_url = api_url_root + config.api_add_suffix
        self._requester = requester or util.get_user_name()
        self._perms_checker = UserPermissionsChecker(config.ingestion_user)
        self._api_url_root = None
        self._chain = None
        self._drs = None

    def _parse_args(self, arg_list=None):

        "Parses arguments and returns parsed args object."

        dirs_help = ("Dataset directory. "
                     "Must have format ${BASEDIR}/${DRS_DIRS}/${VERSION_DIR} "
                     "and any number of directories may be specified,"
                     "except that if --dataset-id is specified then only "
                     "one directory may be specified but there is no requirement "
                     "regarding its format.")

        parser = util.ArgsFromCmdLineOrFileParser('dirs', 'dataset directories', 
                                                  var_meta='directory',
                                                  var_help=dirs_help,
                                                  description=__doc__)

        util.add_project_arg(parser)
        parser.add_standard_arguments()
        util.add_api_root_arg(parser)

        parser.add_argument("--dataset-id", "-d", type=str,
                            metavar='dataset_id',
                            help='dataset ID (including .v<version> part)')

        parser.add_argument("--replica", type='store_true',
                            help='label the dataset as a replica')

        args = parser.parse_args(arg_list or sys.argv[1:])

        if args.dataset_id and len(args.dirs) != 1:
            parser.error("Only one directory can be specified with --dataset-id")

        return args

    
    def _get_dataset_id(self, path, dataset_id=None):
        """
        returns the dataset ID implied by the path, but if dataset_id is specified,
        then just return that instead

        but in either case, raises an exception if it does not look like a valid dataset 
        ID
        """
        
        if dataset_id == None:

            dataset_id = self._drs.dir_to_dataset_id(path)
            if dataset_id == None:
                raise Exception("{} does not look like valid DRS path".format(path))

        else:
            if not self._drs.plausible_dataset_id(dataset_id):
                raise Exception("'{}' does not look like valid dataset ID".format(dataset_id))
        
        return dataset_id


    def _validate_dataset_dir(self, path):
        """
        check that the files under the dataset directory are ingestable
        """

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

        if not os.path.isdir(path):
            raise Exception("not a directory")

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
                    message += ("\n{}Please email support@jasmin.ac.uk "
                                "to ask for user '{}' to be given access to\n"
                                "{}\n{}").format(drawline, config.ingestion_user,
                                                 path, drawline)

            raise Exception(message)


    def _add_dataset_dir(self, path, dataset_id, replica):
        "adds specified dataset directory to publication system and parse the response"
       
        params = {'chain': self._chain,
                  'config': self._configuration,
                  'dataset_id': dataset_id,
                  'directory': path,
                  'requester': self._requester,
                  'replica': replica}
        
        fields = util.do_post_expecting_json(self._api_url_root + config.api_add_suffix,
                                             params,
                                             description='publication system',
                                             compulsory_fields=('status',))
        
        if fields['status'] != 0:
            message = 'publication system did not accept dataset'
            try:
                message += ': ' + fields['message']
            except KeyError:
                pass
            raise Exception(message)


    def run(self):
        args = self._parse_args()
        self._drs, self._chain = util.parse_project_arg(args)
        self._api_url_root = args.api_url_root
        errors = False

        cwd = os.getcwd()
        for path in args.dirs:
            # convert to full path
            if not path.startswith("/"):
                path = os.path.normpath(os.path.join(cwd, path))

            print()
            try:
                dataset_id = self._get_dataset_id(path, args.dataset_id)
            except Exception as exc:
                print("ERROR: getting dataset ID: {}".format(exc))
                errors = True
                continue
            try:
                self._validate_dataset_dir(path)
            except Exception as exc:
                print("ERROR: validating dataset directory {}: {}".format(path, exc))
                errors = True
                continue
            try:
                self._add_dataset_dir(path, dataset_id, args.replica)
            except Exception as exc:
                print("ERROR: adding directory {} as ID {}: {}".format(path, dataset_id, exc))
                errors = True
                continue
            print("INFO: added directory {}\n(dataset id = {}".format(path, dataset_id))
        print()
        sys.exit(1 if errors else 0)


def main():
    adder = MIPAdder()
    adder.run()
    
