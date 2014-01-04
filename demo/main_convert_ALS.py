# -*- coding: utf-8 -*-
# Filename: SLSConverter.py
""" Main program for convert SLS data into dataExchange.
"""
from preprocessing.preprocess import Preprocess
from dataio.data_exchange import DataExchangeFile, DataExchangeEntry

from dataio.file_types import Tiff
from tomoRecon import tomoRecon
from visualize import image

import matplotlib.pyplot as plt
import numpy as np

import os
import h5py

import re

#def main():


filename = '/local/data/databank/ALS_2011/Blakely/blakely_raw/blakelyALS_.tif'
filenamedark = '/local/data/databank/ALS_2011/Blakely/blakely_raw/blakelyALSdrk_.tif'
filenamewhite = '/local/data/databank/ALS_2011/Blakely/blakely_raw/blakelyALSbak_.tif'
ALSlogFile = '/local/data/databank/ALS_2011/Blakely/blakely_raw/blakelyALS.sct'

HDF5 = '/local/data/databank/dataExchange/microCT/blakely_ALS_2011.h5'

verbose = True

if verbose: print filename
if verbose: print ALSlogFile

##dataFolder = '/local/data/Hornby_SLS'
##baseName = 'Hornby_b'


#Read input ALS data
file = open(ALSlogFile, 'r')
if verbose: print '###############################'
for line in file:
    if '-scanner' in line:
        Source = re.sub(r'-scanner ', "", line)
        if verbose: print 'Facility', Source
    
    if '-object' in line:
        Sample = re.sub(r'-object ', "", line)
        if verbose: print 'Sample', Sample
        
    if '-senergy' in line:
        Energy = re.findall(r'\d+.\d+', line)
        if verbose: print 'Energy', Energy[0]
        
    if '-scurrent' in line:
        Current = re.findall(r'\d+.\d+', line)
        if verbose: print 'Current', Current[0]

    if '-nangles' in line:
        Angles = re.findall(r'\d+', line)
        if verbose: print 'Angles', Angles[0]

    if '-i0cycle' in line:
        WhiteStep = re.findall(r'\s+\d+', line)
        if verbose: print 'White Step', WhiteStep[0]

if verbose: print '###############################'
file.close()

dark_start = 0
dark_end = 20
dark_step = 1
white_start = 0
white_end = int(Angles[0]) 
white_step = int(WhiteStep[0])
projections_start = 0
projections_end = int(Angles[0]) + 1

# test
#dark_end = 2
#white_end = 361
#projections_end = 2

mydata = Preprocess()

mydata.read_tiff(filename, projections_start, projections_end, file_name_dark = filenamedark, dark_start = dark_start, dark_end = dark_end, dark_step = dark_step, file_name_white = filenamewhite, white_start = white_start, white_end = white_end, white_step = white_step, zeros = False)


#Write HDF5 file.

# Open DataExchange file
f = DataExchangeFile(HDF5, mode='w') 

# Create HDF5 subgroup
# /measurement/instrument
f.add_entry( DataExchangeEntry.instrument(name={'value': 'Tomcat'}) )

# Create HDF5 subgroup
# /measurement/instrument/source
f.add_entry( DataExchangeEntry.source(name={'value': Source},
                                    date_time={'value': "2011-25-05T19:42:13+0100"},
                                    beamline={'value': "ALS Tomo"},
                                    current={'value': float(Current[0]), 'units': 'mA', 'dataset_opts': {'dtype': 'd'}},
                                    )
)

# Create HDF5 subgroup
# /measurement/instrument/monochromator
f.add_entry( DataExchangeEntry.monochromator(type={'value': 'Unknown'},
                                            energy={'value': float(Energy[0]), 'units': 'eV', 'dataset_opts': {'dtype': 'd'}},
                                            mono_stripe={'value': 'Unknown'},
                                            )
    )


# Create HDF5 subgroup
# /measurement/experimenter
f.add_entry( DataExchangeEntry.experimenter(name={'value':"Jane Waruntorn"},
                                            role={'value':"Project PI"},
                )
    )

# Create HDF5 subgroup
# /measurement/instrument/detector
f.add_entry( DataExchangeEntry.detector(manufacturer={'value':'CooKe Corporation'},
                                        model={'value': 'pco dimax'},
                                        serial_number={'value': '1234XW2'},
                                        bit_depth={'value': 12, 'dataset_opts':  {'dtype': 'd'}},
                                        x_pixel_size={'value': 6.7e-6, 'dataset_opts':  {'dtype': 'f'}},
                                        y_pixel_size={'value': 6.7e-6, 'dataset_opts':  {'dtype': 'f'}},
                                        x_dimensions={'value': 2048, 'dataset_opts':  {'dtype': 'i'}},
                                        y_dimensions={'value': 2048, 'dataset_opts':  {'dtype': 'i'}},
                                        x_binning={'value': 1, 'dataset_opts':  {'dtype': 'i'}},
                                        y_binning={'value': 1, 'dataset_opts':  {'dtype': 'i'}},
                                        operating_temperature={'value': 270, 'units':'K', 'dataset_opts':  {'dtype': 'f'}},
                                        exposure_time={'value': 170, 'units':'ms', 'dataset_opts':  {'dtype': 'd'}},
                                        frame_rate={'value': 3, 'dataset_opts':  {'dtype': 'i'}},
                                        output_data={'value':'/exchange'}
                                        )
    )


f.add_entry(DataExchangeEntry.objective(magnification={'value':10, 'dataset_opts': {'dtype': 'd'}},
                                    )
    )

f.add_entry(DataExchangeEntry.scintillator(name={'value':'LuAg '},
                                            type={'value':'LuAg'},
                                            scintillating_thickness={'value':20e-6, 'dataset_opts': {'dtype': 'd'}},
        )
    )



# Create HDF5 subgroup
# /measurement/sample
f.add_entry( DataExchangeEntry.sample( name={'value':Sample},
                                        description={'value':'rock sample tested at SLS and APS'},
        )
    )



# Create core HDF5 dataset in exchange group for 180 deep stack
# of x,y images /exchange/data
f.add_entry( DataExchangeEntry.data(data={'value': mydata.data, 'units':'counts', 'description': 'transmission', 'axes':'theta:y:x' }))
f.add_entry( DataExchangeEntry.data(data_dark={'value': mydata.dark, 'units':'counts', 'axes':'theta_dark:y:x' }))
f.add_entry( DataExchangeEntry.data(data_white={'value': mydata.white, 'units':'counts', 'axes':'theta_white:y:x' }))
f.add_entry( DataExchangeEntry.data(title={'value': 'tomography_raw_projections'}))

f.close()


###if __name__ == "__main__":
###    main()
