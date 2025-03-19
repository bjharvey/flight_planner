"""Code to include SSH images in flight_planner GUI"""

import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from functools import partial

import tkinter as tk
from tkinter import ttk

from .user_config import (datefmt, ssh_domains, ssh_varnames,
                         ssh_projections)
from .image_utils import harvest_gui, cutout_map, today, set_plotdir



def get_image(datapath, domain=None, var=None, validtime=None,
              just_make_filename=False, check_exists=True):
    """Retrieve a single image.

    Optionally checks if the required file already exists and ignores if yes.

    Plots are saved as <plotdir>/<var>_MonD.png
    """
    figname = '{}_{}.png'.format(var, validtime.strftime('%b%d_%Y'))
    plotdir = set_plotdir(datapath, 'ssh')
    localfigname = os.path.join(plotdir, figname)
                
    if check_exists and os.path.isfile(localfigname):
        print('\nSSH_GET_IMAGE: Found file:\n{}'.format(localfigname))
    else:
        if just_make_filename:
            print('\nSSH_GET_IMAGE: Cannot find file, returning None\n{}'.\
                  format(localfigname))
            return None
        else:
            print('SSH_GET_IMAGE: NOT YET IMPLMENTED IMAGE RETRIEVAL')
    return localfigname


def harvest_date(datapath, domain, validtime,
                 stop=None, finish=None):
    """Retrieve all plots for one domain/validtime."""
    if type(validtime) == str: validtime = datetime.strptime(validtime, datefmt)
    print('\nSSH_HARVEST_DATE({}):\n'.format(validtime))
    for var in ssh_varnames:
        print('\nSSH_HARVEST_DATE({}): Retrieving {} {}\n'.\
              format(validtime, domain, var))
        get_image(datapath, domain, var, validtime)
        if stop is not None:
            if stop():
                print('\nSSH_HARVEST_DATE({}): Stopped'.format(validtime))
                return
    if finish is not None:
        finish()
    print('\nSSH_HARVEST_DATE({}): Finished'.format(validtime))


def plot_image(datapath, domain, varname, validtime, ax, data=None):

    ds = ssh_projections[domain]
    if type(validtime) == str: validtime = datetime.strptime(validtime, datefmt)
    ax.set_title('\nVALID: {}'.\
                 format(validtime.strftime('%HZ %a %d %b %Y')), loc='right')

    # Load image if not provided in data
    if data is None:
        figname = get_image(datapath, domain, varname, validtime,
                            just_make_filename=True)
        if figname is None:
            ax.set_title('SSH: {}\n<no image found>'.format(domain), loc='left')
            return None, []
        data = plt.imread(figname)

    # Reset _threshold for overlaying image - overwise get offset
    # Not sure what's going on here!
    ims = ax.imshow(cutout_map(data, white_thres=0.95), aspect='equal',
                    transform=ds['proj'], origin='upper',
                    extent=ds['orig_extent'])

    ax.set_title('SSH: {}\n{}'.\
                 format(domain, varname),
                 loc='left')
    ims = [ims]
    
    # Colorbar
    if hasattr(ax, 'axcb'):
        ims.append(ax.axcb.imshow(cutout_map(data.transpose(1, 0, 2),
                                             get_colbar=True,
                                             white_thres=0.95)[:-100, ::-1]))

    return data, ims
  
    
def setup_ax(self):
    domain = self.MetVars['ssh']['domain'].get()
    print('\nSSH_SETUP:', domain, self.layout['ax'])
    axpos = self.layout['ax'].copy()
    dy = axpos[3] * 0.2 if self.include_cb else 0
    axpos[1] = axpos[1] + dy           # Add room for colorbar
    axpos[3] = axpos[3] - dy
    ds = ssh_projections[domain]
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
    print('\nSSH_UPDATE:')
    # If this (domain, varname, fcsttime, validtime) is already loaded
    # then use that to avoid reloading
    Vars = {k: v.get() for k, v in self.MetVars['ssh'].items()}
    data0 = self.MetData['ssh'][Vars['domain']][Vars['varname']]
    if Vars['validtime'] in data0.keys():
        data = data0[Vars['validtime']]
    else:
        data = None
    for cf in self.cfs: cf.remove()
    data, cfs = plot_image(self.datapath, **Vars, ax=self.ax, data=data)
    data0[Vars['validtime']] = data
    self.fig.canvas.draw_idle()
    self.cfs = cfs


def shiftVardate(self, var, hrs):
    dt = datetime.strptime(var.get(), datefmt)
    dt += timedelta(hours=hrs)
    var.set(dt.strftime(datefmt))
    update_plot(self)


def setup_tk(self, frame):
    # Tkinter variables
    Vars = {'domain': tk.StringVar(value=ssh_domains[0]),
            'varname': tk.StringVar(value=ssh_varnames[0]),
            'validtime': tk.StringVar(value=today().strftime(datefmt))}
    
    # Create frames for four rows
    frames = []
    for i in range(2):
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
        Box['values'] = globals()['ssh_'+key+'s']
        
    # Row 2: Set validtime
    tk.Label(frames[1], text="VALID", width=self.w10, anchor='e').\
        pack(side=tk.LEFT, **self.pads)
    Entry = tk.Entry(frames[1], textvariable=Vars['validtime'],
                     bg='white', width=2*self.w10)
    Entry.bind('<Return>', partial(update_plot, self))
    Entry.pack(side=tk.LEFT, **self.pads)
    for shift in [-24, 24]:
        tk.Button(frames[1], text='{0:+d}'.format(shift),
                  command=partial(shiftVardate, self, Vars['validtime'], hrs=shift)).\
        pack(side=tk.LEFT, **self.pads)

    # Entries specifies entries in harvest GUI. Needs to match inputs to
    # harvest_date function
    entries = {'domain': Vars['domain'],
               'validtime': Vars['validtime']}
    com = partial(harvest_gui, entries, 'Retrieve SSH images',
                  partial(harvest_date, self.datapath))
    tk.Button(frames[1], command=com, text='Retrieve', width=self.w10).\
        pack(side=tk.LEFT, **self.pads)
        
    self.MetVars['ssh'] = Vars
    self.MetData['ssh'] = {domain: {varname: {} for varname in ssh_varnames}
                          for domain in ssh_domains}