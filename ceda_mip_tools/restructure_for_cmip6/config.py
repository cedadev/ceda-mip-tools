
_filename_format_stem = '{variable_id}_{table_id}_{source_id}_{experiment_id}_{member_id}_{grid_label}'

filename_formats = [_filename_format_stem + '_{period_start}-{period_end}.nc',
                    _filename_format_stem + '.nc']

dataset_id_format = '{mip_era}.{activity_id}.{institution_id}.{source_id}.{experiment_id}.{member_id}.{table_id}.{variable_id}.{grid_label}'
