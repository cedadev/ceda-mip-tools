import sys
import argparse


from request_file_manager import \
    MigrateRequestsManager, RetrieveRequestsManager, RequestStatus
import gws


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
                        help='only show requests with status NOT_STARTED or DOING',
                        action='store_true')

    return parser.parse_args()


def main():

    args = parse_args()
    gws_root = gws.get_gws_root_from_path(args.gws)

    statuses = None
    if args.current:
        statuses = (RequestStatus.NOT_STARTED, RequestStatus.DOING)

    for cls in MigrateRequestsManager, RetrieveRequestsManager:
        mgr = cls(gws_root)
        for req in mgr.scan(all_users = args.all_users,
                            statuses=statuses):
            req.dump()


if __name__ == '__main__':
    main()

