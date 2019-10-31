import os
import sys
import argparse

from ceda_mip_tools.restructure_for_cmip6.dataset_id_getter \
    import DatasetIDGetter


class InvalidMove(Exception):
    pass


class RestructureForCMIP6(object):

    def __init__(self):
        self._args = None
        self._stat_dev_cache = {}
        self._id_getter = None


    def _parse_args(self, arg_list=None):

        parser = argparse.ArgumentParser()

        parser.add_argument('-d', '--directory',
                            metavar='path',
                            default='.',
                            help='base directory to move files to')

        parser.add_argument('-v', '--version',
                            type=int,
                            metavar='yyyymmdd',
                            help='version number (default = today)')

        parser.add_argument('-o', '--output',
                            metavar='path',
                            help=('path of file containing output list '
                                  'of versioned directories'))

        parser.add_argument('-O', '--overwrite',
                            action='store_true',
                            help=('permit overwriting of existing '
                                  'output file'))

        parser.add_argument('-m', '--merge',
                            action='store_true',
                            help=('permit adding to existing '
                                  '(non-empty) version directory'))

        parser.add_argument('paths', nargs='+',
                            type=lambda path: self._is_valid_path(parser, path),
                            metavar='path',
                            help='one or more input paths or directories')

        args = parser.parse_args(arg_list or sys.argv[1:])

        if args.output and not args.overwrite and os.path.exists(args.output):
            parser.error(f"Output file '{args.output}' already exists")

        self._args = args
        return args

    
    def _is_valid_path(self, parser, path):
        if os.path.exists(path):
            return path
        else:
            parser.error(f"Input file/directory {path} does not exist")


    def _add_to_file_set(self, s, val):
        if val in s:
            print(f'warning: ignoring duplicate file: {val}')
        s.add(val)


    def _get_paths(self):
        """
        turn list of paths into set of files, by recursing over any dirs
        """
        all = set()
        for path in self._args.paths:
                
            if os.path.isfile(path):
                self._add_to_file_set(all, path)
            else:
                for root, dirs, files in os.walk(path):
                    for name in files:
                        self._add_to_file_set(all, os.path.join(root, name))
        return all
                        

    def _get_output_dir(self, dataset_id):
        root = self._args.directory
        return os.path.join(root, *dataset_id.split("."))


    def _create_output_dirs(self, dataset_dirs):
        for path in dataset_dirs:
            if os.path.exists(path):
                if os.listdir(path) and not self._args.merge:
                    raise Exception(("adding to non-empty version directory {} "
                                    "not permitted without --merge")
                                    .format(path))
            else:
                os.makedirs(path)


    def _write_output(self, dataset_dirs):
        output_file = self._args.output
        if output_file:
            with open(output_file, "w") as fout:
                for path in sorted(dataset_dirs):
                    fout.write(path + "\n")
        print("{} versioned directories".format(len(dataset_dirs)))


    def _check_write_permissions(self, paths):
        "check write permission on parent directories of all the paths"

        parent_dirs = set((os.path.dirname(path) if '/' in path else '.'
                           for path in paths))
        for parent in parent_dirs:
            if not os.access(parent, os.W_OK):
                raise InvalidMove("no write permission on '{}'".format(parent))
    

    def _stat_dev_with_cache(self, path):
        if path not in self._stat_dev_cache:
            self._stat_dev_cache[path] = self._stat_dev(path)
        return self._stat_dev_cache[path]


    def _stat_dev(self, path):
        return os.stat(path).st_dev


    def _check_same_filesystem(self, path, target_dir):
        if self._stat_dev(path) != self._stat_dev_with_cache(target_dir):
            raise InvalidMove("output is not on same filesystem: {} -> {}"
                              .format(path, target_dir))
            

    def _do_renames(self, paths_to_dataset_dirs):
        for path in sorted(paths_to_dataset_dirs.keys()):
            dataset_dir = paths_to_dataset_dirs[path]
            target = os.path.join(dataset_dir, os.path.basename(path))
            os.rename(path, target)


    def _get_dataset_dirs(self, paths):
        paths_to_ids = dict(((path, self._dataset_id_getter(path))
                                     for path in paths))

        ids = set(paths_to_ids.values())
        ids_to_dirs = dict((id, self._get_output_dir(id))
                            for id in ids)

        dirs = sorted(ids_to_dirs.values())

        paths_to_dirs = \
            dict((path, ids_to_dirs[id])
                 for path, id in paths_to_ids.items())

        return dirs, paths_to_dirs
        

    def run(self):

        self._parse_args()
        self._dataset_id_getter = \
            DatasetIDGetter(version=self._args.version).get_dataset_id

        paths = self._get_paths()
        dataset_dirs, paths_to_dataset_dirs = self._get_dataset_dirs(paths)

        try:
            self._check_write_permissions(paths)
        except InvalidMove as err:
            print(f"file move would fail for following reason:\n{err}")
            sys.exit(1)


        self._create_output_dirs(dataset_dirs)

        try:
            for path, dataset_dir in paths_to_dataset_dirs.items():
                self._check_same_filesystem(path, dataset_dir)

        except InvalidMove as err:
            print(f"file move would fail for following reason:\n{err}")
            print("warning: one or more empty output directories may have "
                  f"been created under {self._args.directory} but no "
                  "files have been moved")
            sys.exit(1)

        
        self._do_renames(paths_to_dataset_dirs)
        

        self._write_output(dataset_dirs)
        

def main():
    rs = RestructureForCMIP6()
    rs.run()


if __name__ == '__main__':
    main()
