

from netCDF4 import Dataset
import argparse
import numpy as np
import os
from datetime import datetime
import pandas as pd


NODATA=-9999

def add_main_metadata(nc_ds):
    nc_ds.ncei_template_version = "NCEI_NetCDF_Swath_Template_v2.0"  
    nc_ds.summary = "The Earth Surface Mineral Dust Source Investigation (EMIT) is an Earth Ventures-Instrument (EVI-4) \
Mission that maps the surface mineralogy of arid dust source regions via imaging spectroscopy in the visible and \
short-wave infrared (VSWIR). Installed on the International Space Station (ISS), the EMIT instrument is a Dyson \
imaging spectrometer that uses contiguous spectroscopic measurements from 410 to 2450 nm to resolve absoprtion \
features of iron oxides, clays, sulfates, carbonates, and other dust-forming minerals. During its one-year mission, \
EMIT will observe the sunlit Earth's dust source regions that occur within +/-52° latitude and produce maps of the \
source regions that can be used to improve forecasts of the role of mineral dust in the radiative forcing \
(warming or cooling) of the atmosphere.\n"


    nc_ds.keywords = "Imaging Spectroscopy, minerals, EMIT, dust, radiative forcing"
    nc_ds.Conventions = "CF-1.63, ACDD-1.3"
    nc_ds.sensor = "EMIT (Earth Surface Mineral Dust Source Investigation)"
    nc_ds.instrument = "EMIT"
    nc_ds.platform = "ISS"

    # Feel free to modify institution
    nc_ds.institution = "NASA Jet Propulsion Laboratory/California Institute of Technology"
    nc_ds.license = "Freely Distributed"
    nc_ds.naming_authority = "LPDAAC"
    dt_now = datetime.utcnow()
    nc_ds.date_created = dt_now.strftime("%Y-%m-%dT%H:%M:%SZ")
    nc_ds.keywords_vocabulary = "NASA Global Change Master Directory (GCMD) Science Keywords"
    nc_ds.stdname_vocabulary = "NetCDF Climate and Forecast (CF) Metadata Convention"

    # Feel free to modify
    nc_ds.creator_name = "Jet Propulsion Laboratory/California Institute of Technology"

    nc_ds.creator_url = "https://www.jpl.nasa.gov/"
    nc_ds.project = "Earth Surface Mineral Dust Source Investigation"
    nc_ds.project_url = "https://emit.jpl.nasa.gov/emit"
    nc_ds.publisher_name = "NASA LPDAAC"
    nc_ds.publisher_url = "https://lpdaac.usgs.gov"
    nc_ds.publisher_email = "lpdaac@usgs.gov"
    nc_ds.identifier_product_doi_authority = "https://doi.org"
    nc_ds.processing_level = "L4"
    
    nc_ds.geospatial_bounds_crs = "EPSG:4326"


    nc_ds.title = "EMIT L4 Earth System Model Products V001; "


def add_variable(nc_ds, nc_name, data_type, long_name, units, data, kargs):
    kargs['fill_value'] = NODATA

    nc_var = nc_ds.createVariable(nc_name, data_type, **kargs)
    if long_name is not None:
        nc_var.long_name = long_name
    if units is not None:
        nc_var.units = units

    if data_type is str:
        for _n in range(len(data)):
            nc_var[_n] = data[_n]
    else:
        nc_var[...] = data
    nc_ds.sync()




ACCEPTED_MINERAL_NAMES = [
    'ill',
    'kao',
    'sme',
    'feo',
    'qua',
    'cal',
    'fel',
    'gyp',
    'Illi',
    'Kaol',
    'Smec',
    'Calc',
    'Quar',
    'Feld',
    'Hema',
    'Gyps',
    'IlHe',
    'KaHe',
    'SmHe',
    'CaHe',
    'QuHe',
    'FeHe',
    'GyHe' 
]


def main():
    parser = argparse.ArgumentParser(description='netcdf conversion')
    parser.add_argument('input_file', type=str)
    parser.add_argument('output_base', type=str)
    parser.add_argument('--dimensions', nargs=5, default=['bins','lon','lat','lev','time'])
    parser.add_argument('--use_dimensions', nargs=5, default=[1,1,1,1,1])
    parser.add_argument('--l4_naming_file', default='data/L4_varnames.csv')
    args = parser.parse_args()

    l4_naming = pd.read_csv(args.l4_naming_file)

    source_dataset = Dataset(args.input_file, 'r')


    resolved_names = []
    leftover_names = []


    #for varname in list(source_dataset.variables):
    for _v, varname in enumerate(l4_naming['Short Name']):
        
        l4_names = []
        l4_longnames = []
        if l4_naming['Mineral Repeat'][_v]:
            for mineral_name in ACCEPTED_MINERAL_NAMES:
                ds_name = varname + "_" + mineral_name
                ds_longname = l4_naming['Long Name'][_v] + " " + mineral_name
                if ds_name in list(source_dataset.variables):
                    l4_names.append(ds_name)
                    l4_longnames.append(ds_longname)
                    resolved_names.append(varname)
        else:
            if varname in list(source_dataset.variables):
                l4_names.append(varname)
                l4_longnames.append(l4_naming['Long Name'][_v])
                resolved_names.append(varname)

        if len(l4_names) > 0:
            # Now make the output
            nc_ds = Dataset(os.path.splitext(args.output_base)[0] + f'_{varname}.nc', 'w', clobber=True, format='NETCDF4')
            add_main_metadata(nc_ds)
            #TODO Add your high level sumary information for the specific model here - we'll automatically fill in per variable later:
            #nc_ds.summary += "This model is the XXXX and works like XXXX"

            #nc_ds.input_description += "This is how this model went from EMIT L3 to the specified input"
            nc_ds.sync()
            for _n, name in enumerate(source_dataset.variables[l4_names[0]].dimensions):
                nc_ds.createDimension(name, source_dataset.dimensions[name].size)


            for _l4, l4_name in enumerate(l4_names):
                add_variable(nc_ds, l4_name, "f4", l4_longnames[_l4], None, source_dataset.variables[l4_name][:], {"dimensions": source_dataset.variables[l4_name].dimensions})

            nc_ds.title += varname
            for _vn, vn in enumerate(l4_naming['Long Name']):
                if vn in varname:
                    nc_ds.summary += '\n' + l4_naming['Description'][_vn]
                    break

            nc_ds.sync()
            nc_ds.close()


    resolved_names = np.unique(np.array(resolved_names)).tolist()
    print(f'Succesfully Resolved: {resolved_names}')
    print(f'\n')
    print(f'Unresolved variables:')
    for varname in zip(l4_naming['Short Name'],l4_naming['Long Name']):
        if varname not in resolved_names:
            print(varname)
    

    




if __name__ == "__main__":
    main()
