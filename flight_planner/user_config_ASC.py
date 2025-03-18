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
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

####################
# General settings #
####################

# Initial projection and extent (lon0, lon1, lat0, lat1)
default_projection = ccrs.Stereographic(central_longitude=0,
                                        central_latitude=55,
                                        globe=None)
initial_extent = [-20, 40, 73, 85]

# Format to use for all date strings
datefmt = '%Y%m%d_%HZ'

# Aircraft (only used to set speeds)
aircraft = 'MASIN'

# Dictionary of aircraft speeds
# Must have a transit speed, but other legtypes can also be defined
legtype_spds = {
    None    : {'transit': 135, # default if no aircraft specified
               'science': 120,
               'special': 120},
    'MASIN' : {'transit': 135, # originally 140
               'science': 120,
               'special': 120},
    }[aircraft]
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
hr123_radii = np.array([1, 2, 3]) * legtype_spds['transit']
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



##############################
# Settings for the MO images #
##############################

#### ACAO svalb and svalb_zoom projections for Arctic Cyclones campaign
mo_campaign = 'acao'
mo_models = ['glm', 'acao_ra2m', 'acao_casim']
mo_figname_templates = {'glm'       : '{}_oper-glm_{}_T{}_{}.png',
                        'acao_ra2m' : '{}_acao_ra2m_{}_T{}_{}.png',
                        'acao_casim': '{}_acao_ral3_{}_T{}_{}.png'}
    
# Specify the projection for each domain - provided by Melissa Brooks
mo_domains = {
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

# Specify plots to include and their cutouts for each domain:
# (1) Get names from filenames on jasmin pages
# (2) Hover mouse over axes corners (e.g. in MS paint) to get pixel positions
a1 = {'xlocs': slice(76, 727+1), 'ylocs': slice(10, 940+1)}
a2 = {'xlocs': slice(76, 727+1), 'ylocs': slice(12, 942+1)}
a3 = {'xlocs': slice(77, 727+1), 'ylocs': slice(10, 940+1)}
b1 = {'xlocs': slice(77, 1003+1), 'ylocs': slice(106, 844+1)}
b2 = {'xlocs': slice(77, 896+1), 'ylocs': slice(132, 784+1)}
b3 = {'xlocs': slice(77, 947+1), 'ylocs': slice(128, 822+1)}
b4 = {'xlocs': slice(77, 846+1), 'ylocs': slice(169, 781+1)}
b5 = {'xlocs': slice(77, 947+1), 'ylocs': slice(130, 824+1)}
b6 = {'xlocs': slice(77, 1003+1), 'ylocs': slice(108, 846+1)}
mo_varnames = {
  'svalb': 
      {'sice_surf'        : a1,
       'RainSnowRates'    : a1,
       'cloud'            : a3,
       'WindSpdDir_10m'   : a2,
       'WindGust_10m'     : a2,
       'WindSpdDir_950hPa': a2,
       'WindSpdDir_850hPa': a2,
       'WindSpdDir_300hPa': a2,
       'PV_tlevs_315.0K'  : a1,
       'WBPT_950hPa'      : a3,
       'dtheta_950hPa'    : a3,
       'BLD'              : a3,
       'TCW'              : a3,
       'CldBase'          : a3,
       'Vis_1.5m'         : a3,
       'T_1.5m'           : a1,
       'TropoZ_kft'       : a3,
       },
   'svalb_zoom': 
      {'sice_surf'        : b1,
       'RainSnowRates'    : b4,
       'cloud'            : b2,
       'WindSpdDir_10m'   : b6,
       'WindGust_10m'     : b5,
       'WindSpdDir_850hPa': b6,
       'WindSpdDir_950hPa': b6,
       'WindSpdDir_300hPa': b6,
       'PV_tlevs_315.0K'  : b1,
       'WBPT_950hPa'      : b3,
       'BLD'              : b3,
       'TCW'              : b3,
       'CldBase'          : b3,
       },
  }
    
# This is a faff... the MO plots don't have these extents exactly (e.g. lower
# boundary should skim 65deg line in svalb_zoom, but it doesn't)
# This is because set_extent only works within GeoAxes._threshold accuracy.
# So, if we use the default _threshold (as presumably MO have) then the map
# extents are not exact but they match the MO plots. However, to get
# plotted curved lines to appear smooth we need to reduce _threshold.
# Possible workarounds:
# 1) use default _threshold (as MO) but modify all line plotting code to
#    interpolate between points
# 2) create temperory figures using the MO setup and extract exact extents
#    values of the extents which can then be used when setting up the plot.
# --> try 2 here:
mo_exact_extents = {}
threshold_scale = 100
for key, dom in mo_domains.items():
    # Set up dummy figure and produce an axes matching the MO (default threshold)
    fig0 = plt.figure()
    ax0 = fig0.add_axes([0, 0, 1, 1], projection=dom['proj'])
    ax0.set_extent(dom['extents'], crs=ccrs.PlateCarree())
    # Get the exact extents used and store so we can use them later
    mo_exact_extents[key] = ax0.get_extent()
    plt.close(fig0)
    # Reduce our threshold value so lines plot smoothly
    dom['proj']._threshold = dom['proj']._threshold / threshold_scale

# Additional lines to plot if cross sections are available
mo_xsecs = [{'pt0': [15.47, -17.81], 'pt1': [78.25, 81.70]}, # LYR to BGNO
            {'pt0': [15.54,  15.54], 'pt1': [70.08, 85.92]}]


##############################
# Settings for the EC images #
##############################

# Specify plots to include and their cutouts for each domain:
# (1) Get names from filenames
# (2) Hover mouse over axes corners (e.g. in MS paint) to get pixel positions
ec_varnames = {
    'arctic': {'medium-snow-sic': {'xlocs': slice(303, 1055+1),
                                   'ylocs': slice(624, 1375+1)},
               'medium-mslp-wind850': {'xlocs': slice(387, 1163+1),
                                       'ylocs': slice(612, 1387+1)},
               'medium-mslp-wind200': {'xlocs': slice(295, 957+1),
                                       'ylocs': slice(669, 1330+1)},
               'medium-z500-t850': {'xlocs': slice(387, 1163+1),
                                    'ylocs': slice(612, 1387+1)},
               'medium-clouds': {'xlocs': slice(348, 1188+1),
                                 'ylocs': slice(580, 1420+1)},
               'medium-simulated-wbpt': {'xlocs': slice(387, 1163+1),
                                         'ylocs': slice(612, 1387+1)},
               'medium-2mt-wind30': {'xlocs': slice(303, 1055+1),
                                     'ylocs': slice(624, 1375+1)},
               'medium-rain-rate': {'xlocs': slice(398, 1237+1),
                                    'ylocs': slice(580, 1420+1)}
               }
    }

ec_domains = {
    'arctic': {'proj' : ccrs.NorthPolarStereo(central_longitude=0,
                                              globe=None),
               'extents': [   -180, 180, 60, 90]},
    }
# Reduce default _threshold value to ensure lines are plotted smoothly
threshold_scale = 100
for key, dom in ec_domains.items():
    dom['proj']._threshold = dom['proj']._threshold / threshold_scale


###############################
# Settings for the SIC images #
###############################

# Specify plots to include and their cutouts for each domain:
# (1) Get names from filenames
# (2) Hover mouse over axes corners (e.g. in MS paint) to get pixel positions
sic_varnames = {
    'arctic': {'col': {'xfracs': np.array([151, 2329+1]) / 2479,
                       'yfracs': np.array([151, 3358+1]) / 3507},
               }
    }

# Get xlims and ylims from coordinates printed in plot
sic_corners = {'arctic': {'lon0': - (29 + 59/60 + 8.321/3600),
                          'lat0': (57 + 11/60 + 35.748/3600),
                          'lon1': (85 + 38/60 + 11.481/3600),
                          'lat1': (66 + 46/60 + 32.424/3600)}}
proj = ccrs.NorthPolarStereo()
sic_corners2 = {domain: [proj.transform_point(sic_corners[domain]['lon0'],
                                              sic_corners[domain]['lat0'],
                                              src_crs=ccrs.PlateCarree()),
                         proj.transform_point(sic_corners[domain]['lon1'],
                                              sic_corners[domain]['lat1'],
                                              src_crs=ccrs.PlateCarree())]
                for domain in sic_corners}

sic_domains = {
    'arctic': {'proj' : ccrs.NorthPolarStereo(),
               'xlims': [sic_corners2['arctic'][0][0],
                         sic_corners2['arctic'][1][0]],
               'ylims': [sic_corners2['arctic'][0][1],
                         sic_corners2['arctic'][1][1]]},
    }
# Reduce default _threshold value to ensure lines are plotted smoothly
threshold_scale = 100
for key, dom in sic_domains.items():
    dom['proj']._threshold = dom['proj']._threshold / threshold_scale