configuration = 'esgf-prod'

api_url_root = 'https://ppln.ceda.ac.uk/api/'
api_add_suffix = 'add_dataset/'
api_query_suffix = 'dataset/'

max_query_datasets = 200
max_requester_len = 32
ingestion_user = 'badc'
timeout = 5.


# A basic check that it looks like a plausible DRS. Does not include the whole DRS
# Dictionary of 
# (facet_number, allowed_values)

projects = {
    'CMIP6': {
        'chain': 'CMIP6-fromdisk',

        'drs': {
            'num_facets': 10,
            'facet_allowed_vals': { 0: ['CMIP6'] ,
                                    1: """AerChemMIP C4MIP CDRMIP CFMIP CMIP CORDEX DAMIP DCPP DynVarMIP
                                              FAFMIP GMMIP GeoMIP HighResMIP ISMIP6 LS3MIP LUMIP OMIP PAMIP
                                              PMIP RFMIP SIMIP ScenarioMIP VIACSAB VolMIP""".split() }
            }
        },

    'PRIMAVERA': {
        'chain': 'PRIMAVERA-fromdisk',

        'drs': {
            'num_facets': 10,
            'facet_allowed_vals': { 0: ['PRIMAVERA'] ,
                                    1: """AerChemMIP C4MIP CDRMIP CFMIP CMIP CORDEX DAMIP DCPP DynVarMIP
                                              FAFMIP GMMIP GeoMIP HighResMIP ISMIP6 LS3MIP LUMIP OMIP PAMIP
                                              PMIP RFMIP SIMIP ScenarioMIP VIACSAB VolMIP primWP5""".split() }
            }
        },


    'CORDEX': {
        'chain': 'CORDEX-fromdisk',
        'drs': {
            'num_facets': 12,
            'facet_allowed_vals': { 0: ['cordex'] ,
                                    2: """AFR-44 AFR-44i ANT-44 ANT-44i ARC-44 ARC-44i AUS-44 AUS-44i CAM-44
                                              CAM-44i CAS-44 CAS-44i EAS-44 EAS-44i EUR-11 EUR-11i EUR-44 EUR-44i MED-44
                                              MED-44i MNA-22 MNA-22i MNA-44 MNA-44i NAM-44 NAM-44i SAM-44 SAM-44i SAM-20
                                              SAM-20i WAS-44 WAS-44i""".split()
                                    }
            }
        },
    }

