import os
import re


class DatasetDRS(object):
    
    def __init__(self, drs_config):
        self._drs_config = drs_config

    def _plausible_facets(self, facets):
        """
        Test if a list of facet values is plausible.
        Returns a boolean
        """

        if len(facets) != self._drs_config['num_facets']:
            return False

        for facet in facets:
            if not facet:
                return False

        for pos, vals in self._drs_config['facet_allowed_vals'].items():

            if facets[pos] not in vals:
                return False

        if not self._is_version_number_facet(facets[-1]):
            return False

        return True


    def _is_version_number_facet(self, val):

        return re.match("^v[0-9]+$", val) != None


    def plausible_dataset_id(self, dataset_id):
        """
        Test if a dataset ID is plausible.
        Returns a boolean
        """
        return self._plausible_facets(dataset_id.split('.'))


    def dir_to_dataset_id(self, dirname):
        """
        Converts a directory name to the dataset ID if it looks like a valid 
        dataset directory name ending with dot-separated facets, otherwise returns None
        """
        elements = os.path.normpath(dirname).split('/')
        num_facets = self._drs_config['num_facets']
        if len(elements) < num_facets:
            return None

        facets = elements[-num_facets :]

        if self._plausible_facets(facets):
            return '.'.join(facets)
        else:
            return None

        
if __name__ == '__main__':
    import config
    drs_config = config.projects["CMIP6"]["drs"]
    d = DatasetDRS(drs_config)
    print(d.dir_to_dataset_id('/tmp/alantest/data/CMIP6/CMIP/NOAA-GFDL/GFDL-AM4/amip/r1i1p1f1/AERmon/pfull/gr1/v20180807'))
