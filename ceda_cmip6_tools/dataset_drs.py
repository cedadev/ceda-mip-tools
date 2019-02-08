import os
import re

import ceda_cmip6_tools.config as config



def plausible_facets(facets):
    """
    Test if a list of facet values is plausible.
    Returns a boolean
    """

    if len(facets) != config.num_facets:
        return False

    for facet in facets:
        if not facet:
            return False

    for pos, vals in config.facet_allowed_vals.items():

        if facets[pos] not in vals:
            return False

    if not is_version_number_facet(facets[-1]):
        return False

    return True


def is_version_number_facet(val):
    
    return re.match("^v[0-9]+$", val) != None


def plausible_dataset_id(dataset_id):
    """
    Test if a dataset ID is plausible.
    Returns a boolean
    """
    return plausible_facets(dataset_id.split('.'))


def dir_to_dataset_id(dirname):
    """
    Converts a directory name to the dataset ID if it looks like a valid 
    dataset directory name ending with dot-separated facets, otherwise returns None
    """
    elements = os.path.normpath(dirname).split('/')
    if len(elements) < config.num_facets:
        return None

    facets = elements[-config.num_facets :]
    
    if plausible_facets(facets):
        return '.'.join(facets)
    else:
        return None

        
if __name__ == '__main__':
    print(dir_to_dataset_id('/tmp/alantest/data/CMIP6/CMIP/NOAA-GFDL/GFDL-AM4/amip/r1i1p1f1/AERmon/pfull/gr1/v20180807'))
