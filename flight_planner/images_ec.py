"""Code to include EC images in flight_planner GUI"""

import requests, os
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from functools import partial
import webbrowser

import tkinter as tk
from tkinter import ttk

from .user_config import (datefmt, ec_domains, ec_varnames,
                         ec_projections)
from .image_utils import harvest_gui, cutout_map, today, set_plotdir



def get_image(datapath, domain=None, var=None, fcsttime=None, validtime=None,
              just_make_filename=False, check_exists=True):
    """Retrieve a single image from EC charts webpage.

    Optionally checks if the required file already exists and ignores if yes.

    Plots are saved as <plotdir>/<domain>/YYYYMMDD_HHZ/*.png
    """
    leadhours = int(round((validtime - fcsttime).total_seconds() / 3600))
    figname = '{}_T{}.png'.format(var, leadhours)
    plotdir = set_plotdir(datapath, 'ec')
    localdir = os.path.join(plotdir, domain, fcsttime.strftime(datefmt))
    localfigname = os.path.join(localdir, figname)
  
    if check_exists and os.path.isfile(localfigname):
        print('\nEC_GET_IMAGE: Found file:\n{}'.format(localfigname))
    else:
        if just_make_filename:
            print('\nEC_GET_IMAGE: Cannot find file, returning None\n{}'.\
                  format(localfigname))
            return None
        else:
            #url = 'https://apps.ecmwf.int/webapps/opencharts-api/v1/products/'
            url = 'https://charts.ecmwf.int/opencharts-api/v1/products'
            url = '{}/{}/?valid_time={}&base_time={}&projection={}'.\
                format(url, var, validtime.strftime('%Y-%m-%dT%H')+'%3A00%3A00Z',
                       fcsttime.strftime('%Y-%m-%dT%H')+'%3A00%3A00Z',
                       'opencharts_' + domain)
            print('\nEC_GET_IMAGE: Retrieving URL\n{}'.format(url))
            req = requests.get(url)
            if req.status_code != 200:
                print('EC_GET_IMAGE: Download Failed, returning None')
                return None
            #print(req.json())
            req = requests.get(req.json()['data']['link']['href'])
            if req.status_code != 200:
                print('EC_GET_IMAGE: Download Failed, returning None')
                return None
            if os.path.exists(localdir) is False:
                print('\nEC_GET_IMAGE: Creating plot directory:\n{}'.format(localdir))
                os.makedirs(localdir, exist_ok=True)
            open(localfigname, 'wb').write(req.content)
            print('EC_GET_IMAGE: Success, saved as {}'.\
                  format(localfigname))
    return localfigname


def harvest_date(datapath, domain, fcsttime,
                 frequency=1, ndays=5,
                 stop=None, finish=None):
    """Retrieve all plots for one domain/fcsttime."""
    if type(fcsttime) == str: fcsttime = datetime.strptime(fcsttime, datefmt)
    nleadtimes = int(frequency) * int(ndays) + 1
    leadtimes = np.arange(0, nleadtimes) * 24 / int(frequency)
    print('\nEC_HARVEST_DATE({}): Leadtimes\n{}\n'.format(fcsttime, leadtimes))
    for var in ec_varnames:
        print('\nEC_HARVEST_DATE({}): Retrieving {} {}\n'.\
              format(fcsttime, domain, var))
        for validtime in [fcsttime + timedelta(hours=i) for i in leadtimes]:
            get_image(datapath, domain, var, fcsttime, validtime)
            if stop is not None:
                if stop():
                    print('\nEC_HARVEST_DATE({}): Stopped'.format(fcsttime))
                    return
    if finish is not None:
        finish()
    print('\nEC_HARVEST_DATE({}): Finished'.format(fcsttime))


def plot_image(datapath, domain, varname, fcsttime, validtime, ax, data=None):

    ds = ec_projections[domain]
    if type(fcsttime) == str: fcsttime = datetime.strptime(fcsttime, datefmt)
    if type(validtime) == str: validtime = datetime.strptime(validtime, datefmt)
    ax.set_title('FCST: {}\nVALID: {}'.\
                 format(fcsttime.strftime('%HZ %a %d %b %Y'),
                        validtime.strftime('%HZ %a %d %b %Y')), loc='right')

    # Load image if not provided in data
    if data is None:
        figname = get_image(datapath, domain, varname, fcsttime, validtime,
                            just_make_filename=True)
        if figname is None:
            ax.set_title('EC: {}\n<no image found>'.format(domain), loc='left')
            return None, []
        data = plt.imread(figname)

    # Reset _threshold for overlaying image - overwise get offset
    # Not sure what's going on here!
    ims = ax.imshow(cutout_map(data),
                    aspect='equal', transform=ds['proj'], origin='upper',
                    extent=ds['orig_extent'])

    leadhours = int(round((validtime - fcsttime).total_seconds() / 3600))
    ax.set_title('EC: {}\n{} (T+{})'.\
                 format(domain, varname, leadhours),
                 loc='left')
    ims = [ims]
    
    # Colorbar
    if hasattr(ax, 'axcb'):
        ims.append(ax.axcb.imshow(cutout_map(data, get_colbar=True)[100:-200]))

    return data, ims
  
    
def setup_ax(self):
    domain = self.MetVars['ec']['domain'].get()
    print('\nEC_SETUP:', domain, self.layout['ax'])
    axpos = self.layout['ax'].copy()
    dy = axpos[3] * 0.2 if self.include_cb else 0
    axpos[1] = axpos[1] + dy           # Add room for colorbar
    axpos[3] = axpos[3] - dy
    ds = ec_projections[domain]
    ax = self.fig.add_axes(axpos, projection=ds['proj'])
    self._add_gridlines(ax)
    ax.set_extent(ds['extents'], crs=ccrs.PlateCarree())
    ds['orig_extent'] = ax.get_extent() # Store for adding png after zooming
    ax.set_extent(self.initial_extent, crs=ccrs.PlateCarree())
    if self.include_cb:
        print('Adding colorbar')
        ax.axcb = self.fig.add_axes([self.layout['ax'][0],
                                     self.layout['ax'][1],
                                     self.layout['ax'][2],
                                     axpos[1] * 0.98 - self.layout['ax'][1]])
        ax.axcb.set_axis_off()
    self.coast = ax.coastlines('50m')
    self.ax = ax


def update_plot(self, key=None, dummy=None):
    """Update met with current state"""
    if key == 'domain':
        self.setup_ax()
        self.update_lines()
        return
    print('\nEC_UPDATE:')
    # If this (domain, varname, fcsttime, validtime) is already loaded
    # then use that to avoid reloading
    Vars = {k: v.get() for k, v in self.MetVars['ec'].items()}
    data0 = self.MetData['ec'][Vars['domain']][Vars['varname']]
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
    Vars = {'domain': tk.StringVar(value=ec_domains[0]),
            'varname': tk.StringVar(value=ec_varnames[0]),
            'fcsttime': tk.StringVar(value=today().strftime(datefmt)),
            'validtime': tk.StringVar(value=today().strftime(datefmt))}
    
    # Create frames for four rows
    frames = []
    for i in range(3):
        frames.append(tk.Frame(frame))
        frames[-1].pack(fill=tk.X)
        
    # Row 1: Select domain and varname from dropdown menus
    widths = {'domain': 2*self.w10, 'varname': 2*self.w10}
    for key in ['domain', 'varname']:
        tk.Label(frames[0], text=key.capitalize(), width=self.w10, anchor='e').\
            pack(side=tk.LEFT, **self.pads)
        Box = ttk.Combobox(frames[0], width=widths[key], textvariable=Vars[key])
        Box.pack(side=tk.LEFT, **self.pads)
        Box.bind('<<ComboboxSelected>>', partial(update_plot, self, key))
        Box['values'] = globals()['ec_'+key+'s']
        
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
    entries = {'domain': Vars['domain'],
               'fcsttime': Vars['fcsttime'],
               'frequency': '1', 'ndays': '5'}
    com = partial(harvest_gui, entries, 'Retrieve EC images',
                  partial(harvest_date, self.datapath))
    tk.Button(frames[1], command=com, text='Retrieve', width=self.w10).\
        pack(side=tk.LEFT, **self.pads)
        
    # Row 3: Set validtime
    tk.Label(frames[2], text="VALID", width=self.w10, anchor='e').\
        pack(side=tk.LEFT, **self.pads)
    Entry = tk.Entry(frames[2], textvariable=Vars['validtime'],
                     bg='white', width=2*self.w10)
    Entry.bind('<Return>', partial(update_plot, self))
    Entry.pack(side=tk.LEFT, **self.pads)
    for shift in [-24, -6, 6, 24]:
        tk.Button(frames[2], text='{0:+d}'.format(shift),
                  command=partial(shiftVardate, self, Vars['validtime'], hrs=shift)).\
        pack(side=tk.LEFT, **self.pads)
    url = 'https://charts.ecmwf.int/'
    tk.Button(frames[2], command=lambda e=url: webbrowser.open_new(e),
              text='Webpage', width=self.w10).pack(side=tk.LEFT, **self.pads)
        
    self.MetVars['ec'] = Vars
    self.MetData['ec'] = {domain: {varname: {} for varname in ec_varnames}
                          for domain in ec_domains}