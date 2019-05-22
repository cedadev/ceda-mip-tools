import sys
import argparse


from ceda_cmip6_tools import gws
from ceda_cmip6_tools.cmip6_migration_request_lib import \
    MigrateRequestsManager, RetrieveRequestsManager, RequestStatus


def parse_args(arg_list = None):
    
    parser = argparse.ArgumentParser(
        arg_list,
        description=('list migration and retrieval requests '))

    parser.add_argument('gws',
                        help='path to group workspace')

    parser.add_argument('-a', '--all-users',
                        help='show requests for all users',
                        action='store_true')

    parser.add_argument('-c', '--current',
                        help='only show requests with status NEW or SUBMITTED',
                        action='store_true')

    return parser.parse_args()


def main():

    args = parse_args()
    gws_root = gws.get_gws_root_from_path(args.gws)

    statuses = None
    if args.current:
        statuses = (RequestStatus.NEW, RequestStatus.SUBMITTED)

    for cls in MigrateRequestsManager, RetrieveRequestsManager:
        mgr = cls(gws_root)
        for req in mgr.scan(all_users=args.all_users,
                            statuses=statuses):
            req.dump()
