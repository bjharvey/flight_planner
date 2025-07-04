"""Code to include MO images in flight_planner GUI"""

import requests, os
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from functools import partial
import webbrowser
import cartopy.feature as cfeature

import tkinter as tk
from tkinter import ttk

from .user_config import (datefmt,
                         mo_models, mo_domains, mo_varnames,
                         mo_campaign, mo_figname_templates,
                         mo_projections, mo_xsecs)
from .image_utils import harvest_gui, cutout_map, today, set_plotdir


def get_image(datapath, campaign=None, model=None, domain=None, var=None,
              fcsttime=None, validtime=None,
              user=None, passwd=None,
              just_make_filename=False, check_exists=True):
    """Retrieve a single image from MO forecasts webpage.

    Optionally checks if the required file already exists and ignores if yes.

    Plots are saved as <plotdir>/<campaign>/img/<model>/YYYYMMDD_HHZ/*.png
    """
    url0 = 'http://gws-access.jasmin.ac.uk/public/mo_forecasts/restricted/'
    if var == 'Orog':
        # Different format for static files
        # Note: for TeamX, glm orog is in glm_short directory
        if model == 'glm':
            url1 = '{}/img/glm_short/'.format(campaign)
        else:
            url1 = '{}/img/{}/'.format(campaign, model)
        figname = mo_figname_templates[model].\
            format(var, 'NoTime', 'NoTime', domain)
    else:
        url1 = '{}/img/{}/{}/'.\
               format(campaign, model, fcsttime.strftime(datefmt))
        leadhours = int(round((validtime - fcsttime).total_seconds() / 3600))
        figname = mo_figname_templates[model].\
            format(var, validtime.strftime(datefmt), leadhours, domain)
    url = url0 + url1 + figname
    plotdir = set_plotdir(datapath, 'mo')
    if var == 'Orog':
        localdir = os.path.join(plotdir, mo_campaign, model)
    else:
        localdir = os.path.join(plotdir, mo_campaign, model,
                                fcsttime.strftime(datefmt))
    localfigname = os.path.join(localdir, figname)
  
    if check_exists and os.path.isfile(localfigname):
        print('MO_GET_IMAGE: Found file:\n{}'.format(localfigname))
    else:
        if just_make_filename:
            print('MO_GET_IMAGE: Cannot find file, returning None\n{}'.\
                  format(localfigname))
            return None
        else:
            print('MO_GET_IMAGE: Retrieving URL\n{}'.format(url))
            req = requests.get(url, auth=(user, passwd))
            if req.status_code != 200:
                print('MO_GET_IMAGE: Download Failed, returning None')
                return None
            else:
                if os.path.exists(localdir) is False:
                    print('MO_GET_IMAGE: Creating plot directory:\n{}'.format(localdir))
                    os.makedirs(localdir, exist_ok=True)
                open(localfigname, 'wb').write(req.content)
                print('MO_GET_IMAGE: Success, saved as {}'.\
                      format(localfigname))
    return localfigname


def harvest_date(datapath, model, domain, fcsttime,
                 frequency=1, ndays=5, user='', passwd='',
                 stop=None, finish=None):
    """Retrieve all images for one model/domain/fcsttime."""
    if type(fcsttime) == str: fcsttime = datetime.strptime(fcsttime, datefmt)
    nleadtimes = int(frequency) * int(ndays) + 1
    leadtimes = np.arange(0, nleadtimes) * 24 / int(frequency)
    print('MO_HARVEST_DATE({}): Leadtimes\n{}\n'.format(fcsttime, leadtimes))
    for var in mo_varnames:
        print('MO_HARVEST_DATE({}): Retrieving {}/{} {}\n'.\
              format(fcsttime, model, domain, var))
        for validtime in [fcsttime + timedelta(hours=i) for i in leadtimes]:
            get_image(datapath, mo_campaign, model, domain, var, fcsttime, validtime,
                      user=user, passwd=passwd)
            if stop is not None:
                if stop():
                    print('MO_HARVEST_DATE({}): Stopped'.format(fcsttime))
                    return
    if finish is not None:
        finish()
    print('MO_HARVEST_DATE({}): Finished'.format(fcsttime))


def plot_image(datapath, model, domain, varname, fcsttime, validtime, ax, data=None):
    """Get a single image and display (if not provided in data) in axes ax."""
    print(f'MO_PLOT_IMAGE({model}, {domain}, {varname}, {fcsttime}, {validtime})')
    ds = mo_projections[domain]
    if type(fcsttime) == str: fcsttime = datetime.strptime(fcsttime, datefmt)
    if type(validtime) == str: validtime = datetime.strptime(validtime, datefmt)
    ax.set_title('FCST: {}\nVALID: {}'.\
                 format(fcsttime.strftime('%HZ %a %d %b %Y'),
                        validtime.strftime('%HZ %a %d %b %Y')), loc='right')
    # Load image if not provided in data
    if data is None:
        figname = get_image(
            datapath, mo_campaign, model, domain, varname, fcsttime, validtime,
            just_make_filename=True)
        if figname is None:
            ax.set_title('MO: {}/{}/{}\n<no image found>'.\
                         format(mo_campaign, model, domain), loc='left')
            return None, []
        data = plt.imread(figname)
    else:
        print('MO_PLOT_IMAGE: Using pre-loaded image')
    # Reset _threshold for overlaying image - overwise get offset
    # Not sure what's going on here!
    ims = ax.imshow(cutout_map(data)[1:, 1:],
                    aspect='equal', transform=ds['proj'], origin='upper',
                    extent=ds['orig_extent'])
    leadhours = int(round((validtime - fcsttime).total_seconds() / 3600))
    ax.set_title('MO: {}/{}/{}\n{} (T+{})'.\
                 format(mo_campaign, model, domain, varname, leadhours),
                 loc='left')
    ims = [ims]
    # Add colorbar
    if hasattr(ax, 'axcb'):
        ims.append(ax.axcb.imshow(cutout_map(data, get_colbar=True)))
    return data, ims
    

def _generate_exact_extents(projection):
    """
    This is a faff...the MO plots don't match the extents exactly (e.g.
    lower boundary should skim 65deg line in svalb_zoom, but it doesn't)
    This is because set_extent only works within GeoAxes._threshold accuracy.
    So, if we use the default _threshold (as presumably MO have) then the map
    extents are not exact but they match the MO plots. However, to get
    plotted curved lines to appear smooth we need to reduce _threshold.
    Possible workarounds:
        1) use default _threshold (as MO) but modify all line plotting code to
        interpolate between points
        2) create temperory figures using the MO setup and extract exact extents
        values of the extents which can then be used when setting up the plot.
        --> use 2 here
    """
    # Set up dummy figure and produce an axes matching the MO (default threshold)
    fig0 = plt.figure()
    ax0 = fig0.add_axes([0, 0, 1, 1], projection=projection['proj'])
    ax0.set_extent(projection['extents'], crs=ccrs.PlateCarree())
    # Get the exact extents used
    exact_extents = ax0.get_extent()
    print('_GENERATE_EXACT_EXTENTS: ', exact_extents)
    plt.close(fig0)
    return exact_extents
  
    
def setup_ax(self):
    domain = self.MetVars['mo']['domain'].get()
    print(f'MO_SETUP_AX: domain={domain}')
    axpos = self.layout['ax'].copy()
    dy = axpos[3] * 0.2 if self.include_cb else 0
    axpos[1] = axpos[1] + dy           # Add room for colorbar
    axpos[3] = axpos[3] - dy
    ds = mo_projections[domain]
    ax = self.fig.add_axes(axpos, projection=ds['proj'])
    self._add_gridlines(ax)
    ax.set_extent(_generate_exact_extents(ds), crs=ds['proj'])
    ds['orig_extent'] = ax.get_extent() # Store for adding png after zooming
    ax.set_extent(self.initial_extent, crs=ccrs.PlateCarree())
    for xsec in mo_xsecs:
        ax.plot(xsec['pt0'], xsec['pt1'], transform=ccrs.Geodetic(),
                c='skyblue', linestyle='dashed')
    if self.include_cb:
        print('MO_SETUP_AX: Adding colorbar')
        ax.axcb = self.fig.add_axes([self.layout['ax'][0],
                                     self.layout['ax'][1],
                                     self.layout['ax'][2],
                                     axpos[1] * 0.98 - self.layout['ax'][1]])
        ax.axcb.set_axis_off()
    self.coast = ax.add_feature(cfeature.BORDERS, linestyle=':')#ax.coastlines('50m')
    self.ax = ax


def update_plot(self, key=None, dummy=None):
    """Update met with current state"""
    if key == 'domain':
        self.setup_ax()
        self.update_lines()
        return
    # If this (model, domain, varname, fcsttime, validtime) is already loaded
    # then use that to avoid reloading
    Vars = {k: v.get() for k, v in self.MetVars['mo'].items()}
    print('MO_UPDATE_PLOT:')
    print(Vars)
    data0 = self.MetData['mo'][Vars['model']][Vars['domain']][Vars['varname']]
    if (Vars['fcsttime'], Vars['validtime']) in data0.keys():
        data = data0[Vars['fcsttime'], Vars['validtime']]
    else:
        data = None
    for cf in self.cfs: cf.remove()
    data, cfs = plot_image(self.datapath, **Vars, ax=self.ax, data=data)
    data0[Vars['fcsttime'], Vars['validtime']] = data
    self.fig.canvas.draw_idle()
    self.cfs = cfs


def shiftVardate(self, var, hrs):
    dt = datetime.strptime(var.get(), datefmt)
    dt += timedelta(hours=hrs)
    var.set(dt.strftime(datefmt))
    update_plot(self)


def setup_tk(self, frame):
    # Tkinter variables
    Vars = {'model': tk.StringVar(value=mo_models[0]),
            'domain': tk.StringVar(value=mo_domains[0]),
            'varname': tk.StringVar(value=mo_varnames[0]),
            'fcsttime': tk.StringVar(value=today().strftime(datefmt)),
            'validtime': tk.StringVar(value=today().strftime(datefmt))}
    
    # Create frames for four rows
    frames = []
    for i in range(3):
        frames.append(tk.Frame(frame))
        frames[-1].pack(fill=tk.X)
        
    # Row 1: Select model, domain and varname from dropdown menus
    widths = {'model': self.w10, 'domain': self.w10, 'varname': 2*self.w10}
    for key in ['model', 'domain', 'varname']:
        tk.Label(frames[0], text=key.capitalize(), width=self.w10, anchor='e').\
            pack(side=tk.LEFT, **self.pads)
        Box = ttk.Combobox(frames[0], width=widths[key], textvariable=Vars[key])
        Box.pack(side=tk.LEFT, **self.pads)
        Box.bind('<<ComboboxSelected>>', partial(update_plot, self, key))
        Box['values'] = globals()['mo_'+key+'s']
        
    # Row 2: Set fcsttime
    tk.Label(frames[1], text="FCST", width=self.w10, anchor='e').\
        pack(side=tk.LEFT, **self.pads)
    Entry = tk.Entry(frames[1], textvariable=Vars['fcsttime'],
                     bg='white', width=2*self.w10)
    Entry.bind('<Return>', partial(update_plot, self))
    Entry.pack(side=tk.LEFT, **self.pads)
    for shift in [-24, -6, 6, 24]:
        tk.Button(frames[1], text='{0:+d}'.format(shift),
                  command=partial(shiftVardate, self, Vars['fcsttime'], shift)).\
        pack(side=tk.LEFT, **self.pads)
    # Entries specifies entries in harvest GUI. Needs to match inputs to
    # harvest_date function
    entries = {'model': Vars['model'], 'domain': Vars['domain'],
               'fcsttime': Vars['fcsttime'],
               'frequency': '1', 'ndays': '5', 'user': '', 'password': ''}
    com = partial(harvest_gui, entries,
                  'Retrieve MO images for campaign {}'.\
                      format(mo_campaign.upper()), partial(harvest_date, self.datapath))
    tk.Button(frames[1], command=com, text='Retrieve', width=self.w10).\
        pack(side=tk.LEFT, **self.pads)
        
    # Row 3: Set validtime
    tk.Label(frames[2], text="VALID", width=self.w10, anchor='e').\
        pack(side=tk.LEFT, **self.pads)
    Entry = tk.Entry(frames[2], textvariable=Vars['validtime'],
                     bg='white', width=2*self.w10)
    Entry.bind('<Return>', partial(update_plot, self))
    Entry.pack(side=tk.LEFT, **self.pads)
    for shift in [-24, -6, -1, 1, 6, 24]:
        tk.Button(frames[2], text='{0:+d}'.format(shift),
                  command=partial(shiftVardate, self, Vars['validtime'], hrs=shift)).\
        pack(side=tk.LEFT, **self.pads)
    url = 'https://gws-access.jasmin.ac.uk/public/mo_forecasts/restricted'\
        '/{}/mo_f_{}_dtime.html'.format(mo_campaign, mo_campaign)
    tk.Button(frames[2], command=lambda e=url: webbrowser.open_new(e),
              text='Webpage', width=self.w10).pack(side=tk.LEFT, **self.pads)
        
    self.MetVars['mo'] = Vars
    self.MetData['mo'] = {model: {domain: {varname: {}
                                           for varname in mo_varnames}
                                  for domain in mo_domains}
                          for model in mo_models}