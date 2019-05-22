import sys
import argparse


from ceda_cmip6_tools import gws
from ceda_cmip6_tools.cmip6_migration_request_lib import MigrateRequestsManager, RetrieveRequestsManager


def parse_args(arg_list = None):
    
    parser = argparse.ArgumentParser(
        arg_list,
        description=('create directories required for migration requests '
                     'for a group workspace '
                     '(to be run by GWS manager)'))

    parser.add_argument('gws',
                        help='path to group workspace')

    return parser.parse_args()


def main():

    args = parse_args()
    gws_root = gws.get_gws_root_from_path(args.gws)

    for cls in MigrateRequestsManager, RetrieveRequestsManager:
        mgr = cls(gws_root)
        mgr.initialise()
