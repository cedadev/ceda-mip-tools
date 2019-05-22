import sys
import argparse


from cmip6_migration_request_lib import MigrateRequestsManager
import gws


def parse_args(arg_list = None):
    
    parser = argparse.ArgumentParser(
        arg_list,
        description='withdraw request to migrate data')

    parser.add_argument('gws',
                        help='path to group workspace')

    parser.add_argument('id',
                        type=int,
                        help='request id')

    return parser.parse_args()


def main():
    args = parse_args()
    gws_root = gws.get_gws_root_from_path(args.gws)    
    mrm = MigrateRequestsManager(gws_root)
    mrm.withdraw(args.id)
    print("withdrew request id={}".format(args.id))


if __name__ == '__main__':
    main()

