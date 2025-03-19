"""
User config file for Arctic Cyclones campaign Summer 2022.

Set up to use data sources:
    MO: ACAO campaign plots on jasmin webpages
            models = global plus 2 x regional
            domains = svalb (global only)
                      svalb_zoom (all three)
    EC: ECCharts plots for 'arctic' domain
"""

import numpy as np
import copy
import cartopy.crs as ccrs

import matplotlib as mpl
mpl.rcParams.update({'font.size': 8})
    
def _reduce_threshold(projin, scale=100):
    # Reduce default _threshold value to ensure lines are plotted smoothly
    projout = copy.copy(projin)
    try: 
        projout._threshold = projout._threshold / scale
    except:
        # ccrs.Miller has no _threshold attribute
        projout.threshold = projout.threshold / scale
    return projout

####################
# General settings #
####################

# Initial projection and extent (lon0, lon1, lat0, lat1)
# (makes sense to match MO projection if using that most)
default_projection = ccrs.Stereographic(central_longitude=0,
                                        central_latitude=55,
                                        globe=None)
initial_extent = [-20, 40, 73, 85]

# Format to use for all date strings
datefmt = '%Y%m%d_%HZ'

# Aircraft (only used to set speeds)
aircrafts = ['MASIN']

# Dictionary of aircraft speeds
# Must have a transit speed, but other legtypes can also be defined
legtype_spds = {
    None    : {'transit': 135, # default if no aircraft specified
               'science': 120,
               'special': 120},
    'MASIN' : {'transit': 135, # originally 140
               'science': 120,
               'special': 120},
    }
legtype_cols = {'transit': 'k', 'science': 'r', 'special': 'b'}

# Dictionary of airport locations (lon, lat, alt [ft])
airports = {
    'ANX' : [ 16.1441676, 69.2925  , 46.0],
    'CNP' : [-22.650556 , 70.743056, 45.0],
    'LYR' : [ 15.465556 , 78.246111, 94.0],
    'BGNO': [-16.677167 , 81.609   , 80.0],
    }

# Airport isochrones based on transit speed.
# Select airports to draw isochrones around and the distances to use
hr123_radii = np.array([1, 2, 3])
hr123_labels = ['1', '2', '3']
airport_isochrones = {'LYR' : (hr123_radii, hr123_labels),
                      'BGNO': (hr123_radii, hr123_labels)}

# FIR boundaries
# These are drawn on the map (connected using straight lines in a PlateCarree
# projection) (in fact, could specify any list of points here to be drawn...)
fir_boundaries = {
    # From Dan B via John; used intdegdecminstr2lonlat to convert
    'bodo': ([(0.0, 82.0), (30.0, 82.0), (30.0, 71.0), (28.0, 71.3333),
             (25.0, 71.3333), (17.9862, 70.472), (15.0, 70.0), (9.4202, 67.25),
             (7.7047, 66.2067), (7.0, 65.75), (6.8377, 65.6177),
             (6.2667, 65.1333), (5.0088, 64.0), (4.0, 63.0), (0.0, 63.0),
             (0.0, 82.0)], 'g'),
    }

# Gridlines (grid1=dashed, grid2=solid)
grid1 = {'xlocs': np.arange(-180, 180, 1),
         'ylocs': np.arange(0, 91, 1)}
grid2 = {'xlocs': np.arange(-180, 180, 5),
         'ylocs': np.arange(0, 91, 5)}


# Specify which Met Options to have available
# To add new Met Options, need to create an XX_images.py file.
met_options = ['mo', 'ec', 'sic']


##############################
# Settings for the MO images #
##############################
    
# Specify models, domains and varnames to include
mo_models = ['glm', 'acao_ra2m', 'acao_casim']
mo_domains = ['UK', 'xUKV']
mo_varnames = ['RainSnowRates', 'cloud',
               'WindSpdDir_10m', 'WindGust_10m', 'WindSpdDir_950hPa',
               'WindSpdDir_850hPa', 'WindSpdDir_300hPa',
               'WBPT_950hPa', 'dtheta_950hPa', 'BLD', 'TCW', 'CldBase',
               'Vis_1.5m', 'T_1.5m']

# Additional info required
mo_campaign = 'acao'
mo_figname_templates = {'glm'       : '{}_oper-glm_{}_T{}_{}.png',
                        'acao_ra2m' : '{}_acao_ra2m_{}_T{}_{}.png',
                        'acao_casim': '{}_acao_ral3_{}_T{}_{}.png'}
mo_projections = {
    'svalb': {'proj' : ccrs.Stereographic(central_longitude=0,
                                          central_latitude=55,
                                          globe=None),
              'extents': [-40, 40, 65, 86]
              },
     'svalb_zoom': {'proj' : ccrs.Stereographic(central_longitude=15,
                                                central_latitude=55,
                                                globe=None),
                    'extents': [-2, 32, 65, 83]
                   },
    }

# Additional lines to plot if cross sections are available
mo_xsecs = [{'pt0': [15.47, -17.81], 'pt1': [78.25, 81.70]}, # LYR to BGNO
            {'pt0': [15.54,  15.54], 'pt1': [70.08, 85.92]}]


##############################
# Settings for the EC images #
##############################

ec_domains = ['arctic']
ec_projections = {'arctic': {
        'proj' : ccrs.NorthPolarStereo(central_longitude=0, globe=None),
        'extents': [   -180, 180, 60, 90]}}
ec_varnames = ['medium-mslp-wind850', 'medium-mslp-wind200',
               'medium-z500-t850', 'medium-clouds',
               'medium-simulated-wbpt', 'medium-2mt-wind30',
               'medium-rain-rate']


###############################
# Settings for the SIC images #
###############################

# Specify domains, projections and varnames
sic_domains = ['arctic']
# Compute projection extents from coordinates printed in plot
sic_corners = {'arctic': {'lon0': - (29 + 59/60 + 8.321/3600),
                          'lat0': (57 + 11/60 + 35.748/3600),
                          'lon1': (85 + 38/60 + 11.481/3600),
                          'lat1': (66 + 46/60 + 32.424/3600)}}
proj = ccrs.NorthPolarStereo()
sic_corners = {domain: [proj.transform_point(sic_corners[domain]['lon0'],
                                             sic_corners[domain]['lat0'],
                                             src_crs=ccrs.PlateCarree()),
                         proj.transform_point(sic_corners[domain]['lon1'],
                                              sic_corners[domain]['lat1'],
                                              src_crs=ccrs.PlateCarree())]
                for domain in sic_domains}
sic_extents = {domain: [sic_corners[domain][0][0], sic_corners[domain][1][0],
                        sic_corners[domain][0][1], sic_corners[domain][1][1]]
               for domain in sic_domains}
sic_projections = {domain: {'proj': proj,
                            'extents': sic_extents[domain]}
                   for domain in sic_domains}
sic_varnames = ['col']