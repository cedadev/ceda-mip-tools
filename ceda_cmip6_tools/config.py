chain = 'CMIP6-user'
configuration = 'esgf-prod'
add_api_url = 'https://ppln.ceda.ac.uk/api/add_dataset/'
query_api_url = 'https://ppln.ceda.ac.uk/api/dataset/'
max_query_datasets = 200
max_requester_len = 32
ingestion_user = 'badc'

num_facets = 10


# A basic check that it looks like a plausible DRS. Does not include the whole DRS
# Dictionary of 
# (facet_number, allowed_values)

facet_allowed_vals = { 0: ['CMIP6'] ,
                       1: """AerChemMIP C4MIP CDRMIP CFMIP CMIP CORDEX DAMIP DCPP DynVarMIP
                           FAFMIP GMMIP GeoMIP HighResMIP ISMIP6 LS3MIP LUMIP OMIP PAMIP
                           PMIP RFMIP SIMIP ScenarioMIP VIACSAB VolMIP""".split() }
