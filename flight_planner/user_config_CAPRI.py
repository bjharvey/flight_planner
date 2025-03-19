"""
Setting up user config file for UKV (CAPRI pilot).

Set up to use data sources:
    MO: main campaign plots on jasmin webpages
            models = glm, ukv
            domains = UK, xUKV
    EC: ECCharts plots for 'arctic' domain - update for nw europe
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
default_projection = ccrs.PlateCarree()
initial_extent = [-20, 3, 47, 62]

# Format to use for all date strings
datefmt = '%Y%m%d_%HZ'

# Aircraft (only used to set speeds)
aircrafts = ['FAAM', 'MASIN']

# Dictionary of aircraft speeds [kts]
# Must have a transit speed, but other legtypes can also be defined here
legtype_spds = {
    'MASIN' : {'transit': 135,
               'science': 120},
    'FAAM' :  {'transit': 270,      # Suggested by Ian
               'science': 194},
    }
legtype_cols = {'transit': 'k', 'science': 'r', 'special': 'b'}

# Dictionary of airport locations (lon, lat, alt [ft])
airports = {
    'CRAN': [-0.616667, 52.0722, 358],
    'BFS' : [-6.215833, 54.6575, 268],
    }

# Airport isochrones based on transit speed.
# Select airports to draw isochrones around and the distances to use
hr123_radii = np.array([1, 2, 3])
hr123_labels = ['1', '2', '3']
airport_isochrones = {'CRAN': (hr123_radii, hr123_labels),
                      'BFS' : (hr123_radii, hr123_labels)}

# FIR boundaries
# These are drawn on the map (connected using straight lines in a PlateCarree
# projection) (in fact, could specify any list of points here to be drawn...)
fir_boundaries = {
    # From Dan B via John
    # Used intdegdecminstr2lonlat to convert
    'bodo': ([(0.0, 82.0), (30.0, 82.0), (30.0, 71.0), (28.0, 71.3333),
             (25.0, 71.3333), (17.9862, 70.472), (15.0, 70.0), (9.4202, 67.25),
             (7.7047, 66.2067), (7.0, 65.75), (6.8377, 65.6177),
             (6.2667, 65.1333), (5.0088, 64.0), (4.0, 63.0), (0.0, 63.0),
             (0.0, 82.0)], 'g'),
    # From: https://nats-uk.ead-it.com/cms-nats/opencms/en/Publications/AIP/Current-AIRAC/html/eAIP/EG-ENR-2.1-en-GB.html
    # See also: https://www.eurocontrol.int/publication/flight-information-region-firuir-charts-2023
    # Used intdegdecminstr2lonlat to convert
    # E.g. copy list of coords then paste into
    # for d in COORDS: print('({}, {}), '.format(*intdegdecminstr2lonlat(d)))
    'Shanwick Oceanic FIR': ([(-30.0, 61.0), 
                              (-10.0, 61.0), 
                              (-10.0, 54.56666666666667), 
                              (-15.0, 54.0), 
                              (-15.0, 51.0), 
                              (-8.0, 51.0), 
                              (-8.0, 45.0), 
                              (-30.0, 45.0), 
                              (-30.0, 61.0)], 'darkblue') ,
    'Shannon FIR': ([(-5.5, 53.916666666666664),  # not on webpage - stiched together surrounding firs
                     (-8.166666666666666, 54.416666666666664),
                     (-6.916666666666667, 55.333333333333336),
                     (-7.333333333333333, 55.416666666666664),
                     (-8.25, 55.333333333333336),
                     (-9.0, 54.75),
                     (-10.0, 54.56666666666667),
                     (-15.0, 54.0), 
                     (-15.0, 51.0), 
                     (-8.0, 51.0),
                     (-5.5, 52.333333333333336),
                     (-5.5, 53.916666666666664)], '0.5'),
    'Scottish FIR' : ([(0.0, 61.0),
                   (0.0, 60.0),
                   (5.0, 57.0),
                   (5.0, 55.0),
                   (-5.5, 55.0),
                   (-5.5, 53.916666666666664),
                   (-8.166666666666666, 54.416666666666664),
                   (-6.916666666666667, 55.333333333333336),
                   (-7.333333333333333, 55.416666666666664),
                   (-8.25, 55.333333333333336),
                   (-9.0, 54.75),
                   (-10.0, 54.56666666666667),
                   (-10.0, 61.0),
                   (0.0, 61.0)], 'g'),
    'London FIR': ([(5.0, 55.0), 
                (2.0, 51.5), 
                (2.0, 51.11666666666667), 
                (1.4666666666666668, 51.0), 
                (1.4666666666666668, 50.666666666666664), 
                (-0.25, 50.0), 
                (-2.0, 50.0), 
                (-8.0, 48.833333333333336), 
                (-8.0, 51.0), 
                (-5.5, 52.333333333333336), 
                (-5.5, 55.0), 
                (5.0, 55.0)], 'darkgreen'),
    
    }

# Gridlines (grid1=dashed, grid2=solid)
grid1 = {'xlocs': np.arange(-180, 180, 1),
         'ylocs': np.arange(0, 91, 1)}
grid2 = {'xlocs': np.arange(-180, 180, 5),
         'ylocs': np.arange(0, 91, 5)}


# Specify which Met Options to have available
# To add new Met Options, need to create an XX_images.py file.
#met_options = ['mo', 'ec', 'sic', 'ssh']
met_options = ['mo', 'ec', 'ssh']


##############################
# Settings for the MO images #
##############################
    
# Specify models, domains and varnames to include
mo_models = ['glm', 'ukv']
mo_domains = ['UK', 'xUKV']
mo_varnames = ['RainSnowRates', 'cloud',
               'WindSpdDir_10m', 'WindGust_10m', 'WindSpdDir_950hPa',
               'WindSpdDir_850hPa', 'WindSpdDir_300hPa',
               'WBPT_950hPa', 'dtheta_950hPa', 'BLD', 'TCW', 'CldBase',
               'Vis_1.5m', 'T_1.5m']

# Additional info required
mo_campaign = 'main'
mo_figname_templates = {'glm': '{}_oper-glm_{}_T{}_{}.png',
                        'ukv': '{}_oper-ukv_{}_T{}_{}.png'}
mo_projections = {'UK': {'proj' : _reduce_threshold(ccrs.PlateCarree()),
                         'extents': [-11, 3, 48, 60]},
                  'xUKV': {'proj' : _reduce_threshold(ccrs.PlateCarree()),
                           'extents': [-25, 16, 44, 63.42]}}

# Additional lines to plot if cross sections are available
mo_xsecs = []


##############################
# Settings for the EC images #
##############################

# Specify domains, projections and varnames
ec_domains = ['north_west_europe']
ec_projections = {'north_west_europe': {
        'proj' : ccrs.NorthPolarStereo(central_longitude=0, globe=None),
        'extents': [-43.4, 40, 69, 46]}}
ec_varnames = ['medium-mslp-wind850', 'medium-mslp-wind200',
               'medium-z500-t850', 'medium-clouds',
               'medium-simulated-wbpt', 'medium-2mt-wind30',
               'medium-rain-rate']


# ###############################
# # Settings for the SIC images #
# ###############################

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


###############################
# Settings for the SSH images #
###############################

# Specify domains, projections and varnames
ssh_domains = ['ne_atlantic']
ssh_projections= {'ne_atlantic': {'proj' : ccrs.Miller(),
                                  'extents': [-30, 10, 40, 66.1]}}
ssh_varnames = ['current_speed', 'ssh']