import os
import pwd
import sys
import argparse
import requests

import ceda_cmip6_tools.config as config


def get_user_name():
    "get a user name (to use as the requester)"
    name = pwd.getpwuid(os.getuid()).pw_gecos
    return name[: config.max_requester_len]


def do_post_expecting_json(url, params, 
                           description="web service",
                           compulsory_fields=()):
    """
    POST the params to the specified URL.
    Return the parsed JSON.
    Raise an exception if any required fields are missing.
    """
    response = requests.post(url, data=params, timeout=config.timeout)

    if response.status_code != 200:
        raise Exception("Could not talk to {}".format(description))
        
    try:
        fields = response.json()
        for key in compulsory_fields:
            dummy = fields[key]
    except (ValueError, KeyError):
        raise Exception("Could not parse response from {}".format(description))
    return fields
    

def paginate_list(lst, count):
    for i in range(0, len(lst), count):
        yield lst[i : i+count]


class ArgsFromCmdLineOrFileParser(object):
    """
    A class which acts like (and encapsulates) an argparse parser.  It allows
    the program to take a list of things that are specified either on the command
    line or in a file which is referenced with --file-from / -f argument, with 
    the special filename "-" for standard input.  Lines from the file are stripped
    of leading/trailing whitespace, and any blank lines are ignored.

    Example:

        parser = ArgsFromCmdLineOrFileParser('things', 'description of thing', 
                                              var_meta='thing',
                                              var_help=help_about_thing,
                                              description=description_of_command)

        parser.add_argument('other_arg')

        args = parser.parse_args(sys.argv[1:])

        print(args.things, args.other_arg)
    
    """
    def __init__(self, var_opt, var_desc, var_meta=None, var_help=None, 
                 allow_empty_list=False, **kwargs):
        self._var_opt = var_opt
        self._var_desc = var_desc
        self._var_help = var_help
        self._var_meta = var_meta
        self._allow_empty_list = allow_empty_list
        self._file_opt = '--from-file'
        self._file_short_opt = '-f'
        self._parser = argparse.ArgumentParser(**kwargs)
        self._add_positional_argument()
        self._add_file_argument()


    def __getattr__(self, k):
        return getattr(self._parser, k)


    def parse_args(self, *pa_args, **pa_kwargs):
        args = self._parser.parse_args(*pa_args, **pa_kwargs)
        self._add_values_from_file(args)
        return args


    def _add_positional_argument(self):
        self._parser.add_argument(self._var_opt, nargs='*',
                                 metavar=self._var_meta,
                                 help=self._var_help)

        
    def _add_file_argument(self):
        help = ("filename to read {} from (or '-' for standard input) "
                "in place of the command line"
                ).format(self._var_desc)
        self._parser.add_argument(self._file_opt, self._file_short_opt,
                                 metavar='filename',
                                 help=help)


    def _add_values_from_file(self, args, abort_on_error=True):
        try:
            self._add_values_from_file_core(args)
        except (ValueError, IOError) as exc:
            print(exc)
            if abort_on_error:
                sys.exit(1)
            else:
                raise


    def _add_values_from_file_core(self, args):
        """
        appends to list based on the --file-option option
        """
        filename = getattr(args, self._file_opt[2:].replace('-', '_'))
        values = getattr(args, self._var_opt)
        if values and (filename != None):
            raise ValueError(('{} cannot be given on command line if {} is used'
                              ).format(self._var_desc, self._file_opt))
        if filename:
            if filename == '-':
                fh = sys.stdin    
            else:
                fh = open(filename)
            with fh:
                for line in fh:
                    val = line.strip()
                    if val:
                        values.append(val)

        if not values and not self._allow_empty_list:
            raise ValueError(('no {} specified - must specify one or more on command line '
                              'or with {} option'
                              ).format(self._var_desc, self._file_opt))
