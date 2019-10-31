"""
parser that converts dataset ID
"""

import os
import re
import netCDF4
import time

from ceda_mip_tools.restructure_for_cmip6 import config


class DatasetIDGetterException(Exception):
    pass


class DatasetIDGetter(object):

    def __init__(self, version=None):

        self._dataset_id_facets = \
            self._get_facet_names_from_template(config.dataset_id_format)

        self._filename_matchers = \
            [re.compile(self._template_to_regexp(fmt)).match
             for fmt in config.filename_formats]

        self._version = (int(version) if version != None 
                         else int(time.strftime("%Y%m%d")))


    _token_re = '{([^}]+)}'

    def get_dataset_id(self, path, version=None):
        "get dataset ID for path"
        facets = self._get_facets(path)
        unversioned_id = config.dataset_id_format.format(**facets)
        return "{}.v{}".format(unversioned_id, 
                               version if version != None else self._version)


    def _template_to_regexp(self, template):
        return re.sub(self._token_re, r'(?P<\1>.*?)', template)
    
    def _get_facet_names_from_template(self, template):
        return [m.group(1) for m in 
                re.finditer(self._token_re, template)]

        
    def _parse_from_file_path(self, path):
        """
        returns dictionary of facets extracted from path
        (whatever the template specifies, not necessarily all the
        facets needed to construct a dataset ID)
        """
        return self._parse_from_file_name(os.path.basename(path))


    def _parse_from_file_name(self, filename):
        for matcher in self._filename_matchers:
            m = matcher(filename)
            if m:
                return m.groupdict()
        raise DatasetIDGetterException("cannot parse filename {} into facets"
                             .format(filename))
            
            
    def _parse_from_netcdf_attributes(self, path):
        """
        returns dictionary of facets extracted from the netCDF
        attributes, based on the set of facets needed to construct 
        a dataset ID, with None for any that were not found
        """
        with netCDF4.Dataset(path) as ds:
            return dict([(key, getattr(ds, key, None)) 
                         for key in self._dataset_id_facets])

    def _get_facets(self, path):
        from_path = self._parse_from_file_path(path)
        from_contents = self._parse_from_netcdf_attributes(path)

        all = {}
        for key, val in from_contents.items():
            if val == None:
                # not extracted from contents - must extract from path name
                if key in from_path:
                    val_used = from_path[key]
                else:
                    raise DatasetIDGetterException(
                        'value of {} not found for file {}'.format(key, path))
            else:
                # extracted from contents
                # if also extracted from path name then check it matches
                if key in from_path:
                    val2 = from_path[key]
                    if val != val2:
                        raise DatasetIDGetterException(
                            ('for file {} mismatch of {} '
                             'from file contents ({}) and from pathname ({})')
                            .format(path, key, val, val2))
                val_used = val

            all[key] = val_used
        return all
            



if __name__ == '__main__':

    import glob

    fp = DatasetIDGetter()

    for path in glob.glob("testdata/*"):
        print(path)
        print(fp.get_dataset_id(path))
        print()
