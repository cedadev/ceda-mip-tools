"""
Checks the publication status of MIP dataset(s)
"""

import os
import sys
import requests
import argparse
import json
import csv

from ceda_mip_tools.pub_sys_intfc import config, util


_statuses = ['not_started', 'in_progress', 'completed', 'failed', 'ALL']

class MIPStatusChecker(object):

    def __init__(self,
                 configuration=config.configuration):
        self._configuration = configuration
        self._api_url_root = None        


    def _parse_args(self, arg_list=None):

        "Parses arguments and returns parsed args object."

        dataset_spec_help = ("This should be the dataset identifier (dot-separated "
                             "string of facet sending .v<version>), e.g. as reported by "
                             "add-mip-dataset although a directory path with the format "
                             "${BASEDIR}/${DRS_DIRS}/${VERSION_DIR} "
                             "will be accepted as an alternative. "
                             "Any number of dataset IDs may be specified.")

        parser = util.ArgsFromCmdLineOrFileParser('dataset_specs', 'dataset specifiers', 
                                                  var_meta='dataset_spec',
                                                  var_help=dataset_spec_help,
                                                  description=__doc__,
                                                  allow_empty_list=True)

        util.add_project_arg(parser)
        parser.add_standard_arguments()
        util.add_api_root_arg(parser)

        group = parser.add_mutually_exclusive_group()
        group.add_argument('--json', '-j', metavar='filename', 
                           help="write output in JSON format to specified file ('-' for standard output)")
        group.add_argument('--csv', '-c', metavar='filename', 
                           help="write output in CSV format to specified file ('-' for standard output)")

        parser.add_argument('--overwrite', '-O', action='store_true', help='overwrite existing output file')

        parser.add_argument('--status', '-s', metavar='status', 
                            choices=_statuses,
                            help=('Show all your datasets with the specified status. (Must be one of {}.) '
                                  'This argument should be used in place of specifying the dataset IDs.'
                                  ).format(_statuses))

        parser.add_argument('--requester', type=str, metavar='requester',
                            help='show datasets for another requester')

        args = parser.parse_args(arg_list or sys.argv[1:])

        if not args.dataset_specs and not args.status:
            raise ValueError("You should either specify dataset IDs or a processing status to search for.\n"
                             "Re-run with -h for a full usage message.")
        
        if args.dataset_specs and args.status:
            raise ValueError("You cannot specify both the dataset IDs and the processing status to search for.")

        return args

    
    def _get_dataset_id(self, dataset_spec):
        "Turn a dataset spec (dataset ID or doc string) into a dataset ID"

        if '/' in dataset_spec:
            dataset_id = self._drs.dir_to_dataset_id(dataset_spec)
            if dataset_id == None:
                raise ValueError(("{} looks like a directory but cannot be mapped into a dataset ID"
                                  ).format(dataset_spec))
            else:
                return dataset_id
        elif '*' in dataset_spec:
            raise ValueError('wildcard in dataset spec is not supported')
        elif self._drs.plausible_dataset_id(dataset_spec):
            return dataset_spec

        else:
            raise ValueError(("{} does not looks like a valid dataset identifier"
                              ).format(dataset_spec))


    def _get_dataset_ids(self, args):
        return [self._get_dataset_id(spec) for spec in args.dataset_specs]


    def _get_dataset_statuses_page(self, dataset_ids):
        "Query the API for multiple datasets, and get the status string (or None if not found)"

        query_params = { 'dataset_id': ','.join(dataset_ids),
                         'chain': self._chain,
                         'configuration': self._configuration,
                         'requester': self._requester,
                         'max_items': len(dataset_ids) }

        fields = self._get_response(query_params)

        # this following assertion would fail if either:
        # - dataset ID matches more than one dataset (it shouldn't because configuration is in the query)
        # - or if server disallows the number we asked for simultaneously
        assert(len(fields['datasets']) == fields['num_found'])

        results_dict = dict((ds['dataset_id'], ds['status']) for ds in fields['datasets'])

        return [(dataset_id, results_dict.get(dataset_id, 'UNKNOWN'))
                for dataset_id in dataset_ids]


    def _get_dataset_statuses(self, dataset_ids):
        results = []
        for page in util.paginate_list(dataset_ids, config.max_query_datasets):
            results.extend(self._get_dataset_statuses_page(page))
        return results


    def _get_results_for_status(self, status):
        """Query the API for all datasets with specified status, 
        and translate the results into a _Results object"""

        query_params = { 'dataset_id': '**',
                         'chain': self._chain,
                         'configuration': self._configuration,
                         'requester': self._requester}
        
        if status != 'ALL':
            query_params['status'] = status


        # paginated query
        # on the last page, 'cursor' is not set, and it will return
        all = []
        while True:
            fields = self._get_response(query_params)
            
            all.extend(((ds['dataset_id'], ds['status'])
                        for ds in fields['datasets']))
            
            if 'cursor' in fields:
                if 'cursor' in query_params:
                    # sanity check against infinite loop
                    assert(query_params['cursor'] != fields['cursor'])
                query_params['cursor'] = fields['cursor']
            else:
                return all


    def _get_response(self, query_params):
        
        return util.do_post_expecting_json(self._api_url_root + config.api_query_suffix,
                                           query_params,
                                           description='publication system',
                                           compulsory_fields=('datasets', 'num_found'))

    def run(self):
        try:
            args = self._parse_args()
            self._drs, self._chain = util.parse_project_arg(args)
            dataset_ids = self._get_dataset_ids(args)
        except ValueError as exc:
            print(exc)
            sys.exit(1)

        self._api_url_root = args.api_url_root

        if args.requester:
            self._requester = args.requester
        else:
            self._requester = util.get_user_name()

        dataset_ids = self._get_dataset_ids(args)
        
        if dataset_ids:
            results = self._get_dataset_statuses(dataset_ids)
        else:
            results = self._get_results_for_status(args.status)

        results = _ResultsWriter(results)
        
        if args.overwrite:
            results.allow_overwrite()

        if args.csv:
            results.write_csv(args.csv)

        elif args.json:
            results.write_json(args.json)

        else:
            results.dump()



class _ResultsWriter(object):

    def __init__(self, results):
        self.results = list(results)
        self._overwrite = False

    _headers = ['Count', 'Dataset ID', 'Status']

    def _get_rows(self):
        for i, (dsid, status) in enumerate(self.results, start=1):
            yield (i, dsid, status)

    def dump(self, writer=print):
        if self.results:
            writer("Publication status for {} MIP datasets:".format(len(self.results)))
            width = max((len(dsid) for dsid, status in self.results))
            formatter = "{:5}  {:{width}}  {}".format
            writer(formatter(*self._headers, width=width))
            line = "=" * (20 + width)
            writer(line)
            for row in self._get_rows():
                writer(formatter(*row, width=width))
            writer(line)
        else:
            writer("No matching datasets")

    def allow_overwrite(self, val=True):
        self._overwrite = val

    def _get_write_fh(self, path):
        if path == '-':
            return sys.stdout
        else:
            if os.path.exists(path) and not self._overwrite:
                raise Exception("Not overwriting file {}".format(path))
            return open(path, "w")            

    def write_csv(self, path):
        with self._get_write_fh(path) as f:
            row_writer = csv.writer(f).writerow
            row_writer(self._headers)
            for row in self._get_rows():
                row_writer(row)
        if path != '-':
            print('wrote ' + path)

    def write_json(self, path):
        all = {}
        datasets = []
        headers = [s.lower().replace(' ', '_') for s in self._headers]
        for row in self._get_rows():
            datasets.append(dict(zip(headers, row)))
        all['datasets'] = datasets
        all['num_found'] = len(datasets)
        with self._get_write_fh(path) as f:
            f.write(json.dumps(all) + "\n")
        if path != '-':
            print('wrote ' + path)


def main():
    checker = MIPStatusChecker()
    checker.run()
    


