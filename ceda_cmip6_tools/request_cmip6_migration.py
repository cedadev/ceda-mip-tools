import sys
import argparse


from ceda_cmip6_tools import gws
from ceda_cmip6_tools.cmip6_migration_request_lib import MigrateRequestsManager


def parse_args(arg_list = None):
    
    parser = argparse.ArgumentParser(
        arg_list,
        description='request data migration')

    parser.add_argument('directory',
                        help='directory to migrate')

    return parser.parse_args()


def main():
    
    args = parse_args()

    gws_root = gws.get_gws_root_from_path(args.directory)
    
    rrm = MigrateRequestsManager(gws_root)

    request = rrm.create_request(args.directory)

    print("created request")
    request.dump()
