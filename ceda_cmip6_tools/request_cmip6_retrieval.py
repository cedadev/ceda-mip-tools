import sys
import argparse


from ceda_cmip6_tools import gws
from ceda_cmip6_tools.cmip6_migration_request_lib import RetrieveRequestsManager


def parse_args(arg_list = None):
    
    parser = argparse.ArgumentParser(
        arg_list,
        description='request retrieval of migrated data')

    parser.add_argument('orig_dir',
                        help='directory which was migrated')

    parser.add_argument('dest_dir',
                        nargs='?',
                        help=('optional directory to retrieve to '
                              '(by default, retrieve to original location)'))

    return parser.parse_args()


def main():
    
    args = parse_args()

    gws_root = gws.get_gws_root_from_path(args.orig_dir)
    
    if (args.dest_dir and 
        gws.get_gws_root_from_path(args.dest_dir) != gws_root):
        raise Exception("You cannot restore to a different Group Workspace.")
    
    rrm = RetrieveRequestsManager(gws_root)

    request = rrm.create_request(args.orig_dir, args.dest_dir)

    print("created request")
    request.dump()
