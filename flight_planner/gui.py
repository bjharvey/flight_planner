import os
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import importlib, webbrowser, datetime

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.widgets import RadioButtons
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.geodesic as cgeodesic
from cartopy.io.img_tiles import GoogleTiles
import shapely

from .flightdef import (FlightDef, is_near_airport, is_near_other_waypoints,
                        nm2km, km2nm, WayPoint_from_repr, locked_WayPoint,
                        greatcircle, loaddat, loadgpx)
from .user_config import (default_projection, initial_extent, datefmt,
                          aircrafts, legtype_spds, legtype_cols,
                          airports, airport_isochrones, fir_boundaries,
                          grid1, grid2, met_options)

# Import met modules based on the met_options selected in user_config
met_mods = {}
for met_option in met_options:
    met_mods[met_option] = importlib.import_module('.images_' + met_option, 'flight_planner')

wplock = 10   # lock to airports and other waypoints if witihin wplock km
debug = False # print messages when executing canvas update events


class PlannerGUI(tk.Tk):
    """
    Flight planner GUI for interactive click-and-drag flight planning.
    """

    def __init__(self):
        super().__init__()

        # Get path from user for data
        self.set_datapath()
        
        # Detect screen size and set tk window size as fraction of screen
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        scaled_geom = '{}x{}'.format(int(0.80 * self.screen_width),
                                     int(0.6 * self.screen_height))
        print('PlannerGUI: Using geometry {}'.format(scaled_geom))
        self.geometry(scaled_geom)
        self.title("Flight Planner")

        # Initiate empty flight definition
        self.flightdef = FlightDef(
            waypoints=[], name='MMDDa', aircraft=aircrafts[0],
            legtype_spds=legtype_spds[aircrafts[0]], datapath=self.datapath)

        # Setup tk widgets
        self.setup_tk()

        # Setup matplotlib figure
        self.setup_ax()

    def set_datapath(self):
        # Prompt user to select file location
        self.datapath = filedialog.askdirectory(initialdir=os.getcwd(),
                                                title='Enter location for saving flight defs and met images...')

    def setup_tk(self):
        """Setup tkinter window"""
        print('SETUP_TK: Setting up tkinter objects')
        
        # Setup screen dependent widths and fontsize
        base_width = 2736 # Screen width used for testing
        w10 = int(16 * self.screen_width / base_width)
        w6 = int(9 * self.screen_width / base_width)
        pads = {'padx': 5, 'pady': 5}
        fontsize = int(15 * self.screen_width / base_width)
        self.option_add('*font', 'ubuntu '+str(fontsize))
        # Store for use in images_*.py routines
        self.pads, self.w6, self.w10 = pads, w6, w10
        
        # Set up left and right hand frames
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        frameL = tk.Frame(self)
        frameL.grid(row=0, column=0, sticky='nsw')
        frameR = tk.Frame(self)
        frameR.grid(row=0, column=1, sticky='nesw')

        # Flight Defition and Map Control frames (RHS)
        tk.Frame(frameR, height=1, bg="black").pack(fill=tk.X)
        frameFDs = []
        for i in range(6):
            frameFDs.append(tk.Frame(frameR))
            frameFDs[-1].pack(fill=tk.X)
        tk.Frame(frameR, height=1, bg="black").pack(fill=tk.X)
        frameMCs = []
        for i in range(4):
            frameMCs.append(tk.Frame(frameR))
            frameMCs[-1].pack(fill=tk.X)
        tk.Frame(frameR, height=1, bg="black").pack(fill=tk.X)
            
        # tk variables
        self.nameVar = tk.StringVar()
        self.aircraftVar = tk.StringVar()
        self.metVar = tk.StringVar(value='nomet')
        
        frame = frameFDs[0]
        tk.Label(frame, text="Flight Definition", width=2*w10, anchor='w').\
            pack(side=tk.LEFT, **pads)
        tk.Button(frame, text='Help', command=self.help, width=w6).\
            pack(side=tk.RIGHT, **pads)
        tk.Button(frame, text='View in Windy', command=self.windy, width=3*w6).\
            pack(side=tk.RIGHT, **pads)
        tk.Button(frame, text='Load', command=self.load, width=w6).\
            pack(side=tk.RIGHT, **pads)
        tk.Button(frame, text='Save', command=self.save, width=w6).\
            pack(side=tk.RIGHT, **pads)
        
        frame = frameFDs[1]
        tk.Label(frame, text="Name", width=w10, anchor='e').\
            pack(side=tk.LEFT, **pads)
        Entry = tk.Entry(frame, text=self.nameVar, bg='white', width=w10)
        Entry.bind('<Return>', self.update_flightdef)
        Entry.pack(side=tk.LEFT, **pads)
        tk.Label(frame, text="Aircraft", width=w10, anchor='e').\
            pack(side=tk.LEFT, **pads)
        Box = ttk.Combobox(frame, width=w10, textvariable=self.aircraftVar)
        Box.pack(side=tk.LEFT, **self.pads)
        Box.bind('<<ComboboxSelected>>', self.update_flightdef)
        Box['values'] = aircrafts
        #self.legtypeLabel = tk.Label(frame)
        #self.legtypeLabel.pack(side=tk.LEFT, **pads)
        
        frame = frameFDs[2]
        tk.Label(frame, text='Summary', width=w10, anchor='e').\
            pack(side=tk.LEFT, **pads)
        self.summaryLabel = tk.Label(frame)
        self.summaryLabel.pack(side=tk.LEFT, **pads)
        
        frame = frameFDs[3]
        tk.Label(frame, text="WayPoints", width=w10, anchor='ne').\
            pack(side=tk.LEFT, fill=tk.Y, **pads)
        # Can't use StringVar with ScrolledText?
        self.flightdefST = scrolledtext.ScrolledText(
            frame, font=('Courier', 10), bg='white', height=2*w10)
        self.flightdefST.pack(fill=tk.X, expand=True, **pads)
        
        frame = frameFDs[5]
        tk.Button(frame, text='Update FlightDef',
                  command=self.update_flightdef).\
            pack(side=tk.LEFT, fill=tk.X, expand=True, **pads)
        tk.Button(frame, text='Print FlightDef',
                  command=self.print_flightdef).\
            pack(side=tk.LEFT, fill=tk.X, expand=True, **pads)
        tk.Button(frame, text='Relabel WayPoints',
                  command=self.relabel_waypoints).\
          pack(side=tk.LEFT, fill=tk.X, expand=True, **pads)
        tk.Button(frame, text='Clear FlightDef',
                  command=self.clear_flightdef).\
          pack(side=tk.LEFT, fill=tk.X, expand=True, **pads)
          
        frame = frameMCs[0]        
        tk.Label(frame, text="Map Control", width=2*w10, anchor='w').\
            pack(side=tk.LEFT, **pads)

        frame = frameMCs[1]
        tk.Label(frame, text="Features:", width=w10, anchor='ne').\
            pack(side=tk.LEFT, fill=tk.Y, **pads)
        self.toggles = {}
        for key in ['grid', 'coast', 'airports', 'image', 'colorbar']:
            ToggleVar = tk.IntVar()
            Check = tk.Checkbutton(frame, text=key.capitalize(),
                                    command=getattr(self, 'toggle_'+key),
                                    variable=ToggleVar, onvalue=1, offvalue=0)
            Check.pack(side=tk.LEFT, **self.pads)
            # Set startup values
            if key == 'colorbar':
                Check.deselect()
            else:
                Check.select()
            self.toggles[key] = ToggleVar
            
        frame = frameMCs[2]
        tk.Label(frame, text="Met Image:", width=w10, anchor='ne').\
            pack(side=tk.LEFT, fill=tk.Y, **pads)
        tk.Radiobutton(frame, text='None', variable=self.metVar,
                        value='nomet', command=self.toggle_met).\
            pack(side=tk.LEFT)
        for met_option in met_options:
            tk.Radiobutton(
                frame, text=met_option.upper(),
                variable=self.metVar, value=met_option,
                command=self.toggle_met).pack(side=tk.LEFT)

        # Met frame (RHS, lower)
        frame = frameMCs[3]
        self.metframes = {}
        self.MetVars = {'nomet': {}}
        self.MetData = {'nomet': {}}
        self.include_cb = False
        for met_option in met_options:
            self.metframes[met_option] = tk.Frame(frame)
            met_mods[met_option].setup_tk(self, self.metframes[met_option])

        # Map frame (LHS)
        self.fig = Figure(figsize=[0.8 * self.screen_width / 2 / 100,
                                   0.9 * self.screen_height / 2 / 100],
                          dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, frameL)
        self.set_default_filename()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH)
        toolbar_frame = tk.Frame(frameL)
        toolbar_frame.pack(fill=tk.X)
        NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.update_info()

    def toggle_met(self):
        """Toggle met frames and redraw ax"""
        print('TOGGLE_MET: Switching to {}'.format(self.metVar.get()))
        for met_option in met_options:
            if self.metVar.get() == met_option:
                self.metframes[met_option].pack(fill=tk.BOTH, expand=True)
            else:
                self.metframes[met_option].pack_forget()
        # Retain fcsttime and validtime if present
        if hasattr(self, 'prevmet'):
            for key in 'fcsttime', 'validtime':
                if key in self.MetVars[self.metVar.get()].keys() and \
                    key in self.MetVars[self.prevmet].keys():
                        print('TOGGLE_MET: Retaining {}'.format(key))
                        self.MetVars[self.metVar.get()][key].set(
                            self.MetVars[self.prevmet][key].get())
        self.prevmet = self.metVar.get()
        self.setup_ax()
        self.update_lines()

    def toggle_grid(self):
        for grid in self.gridlines:
            grid._draw_gridliner() # the line_artists arent always drawn, why?
            grid.xline_artists[0].\
                set_visible(not grid.xline_artists[0].get_visible())
            grid.yline_artists[0].\
                set_visible(not grid.yline_artists[0].get_visible())
        self.fig.canvas.draw_idle()

    def toggle_coast(self):
        self.coast.set_visible(not self.coast.get_visible())
        self.fig.canvas.draw_idle()
        
    def toggle_airports(self):
        for airport_object in self.airport_objects:
            airport_object.set_visible(not airport_object.get_visible())
        self.fig.canvas.draw_idle()

    def toggle_image(self):
        for cf in self.cfs:
            cf.set_visible(not cf.get_visible())
        self.fig.canvas.draw_idle()
    
    def toggle_colorbar(self):
        self.include_cb = not self.include_cb
        self.setup_ax()
        self.update_lines()
    
    def _add_gridlines(self, ax=None):
        # Add gridlines - do in function so can call from met_images code
        # Need to do this so can call _draw_gridliner before set_extent so
        # that all gridlines are drawn and not just those in the intial_extent
        # domain.
        if ax is None: ax=self.ax
        gridlines1 = ax.gridlines(xlocs=grid1['xlocs'],
                                  ylocs=grid1['ylocs'],
                                  color='0.5', linestyle='--')
        gridlines2 = ax.gridlines(xlocs=grid2['xlocs'],
                                  ylocs=grid2['ylocs'],
                                  color='0.2', linestyle='-')
        self.gridlines = [gridlines1, gridlines2]
        for grid in self.gridlines: grid._draw_gridliner()
        

    def setup_ax(self):
        """Setup map and timeseries axes"""
        print('\nSETUP_AX: Setting up figure axes for met={}'.\
              format(self.metVar.get()))

        # Remove all axes
        for ax in self.fig.axes: ax.remove()

        self.layout = {'ax'      : [0.02, 0.18, 0.96, 0.7],
                       'tsax'    : [0.10, 0.07, 0.75, 0.10],
                       'tsxvarbn': [0.86, 0.07, 0.12, 0.10]}
        self.cfs = []
        self.initial_extent = initial_extent

        # Setup map axes        
        if self.metVar.get() == 'nomet':
            self.ax = self.fig.add_axes(
                self.layout['ax'], projection=default_projection)
            self._add_gridlines()
            self.ax.set_extent(self.initial_extent, crs=ccrs.PlateCarree())
            self.cfs = [self.ax.add_feature(cfeature.LAND),
                        self.ax.add_feature(cfeature.OCEAN),
                        #self.ax.add_feature(cfeature.COASTLINE),
                        self.ax.add_feature(cfeature.BORDERS, linestyle=':'),
                        self.ax.add_feature(cfeature.LAKES, alpha=0.5),
                        #self.ax.add_feature(cfeature.RIVERS),
                        ]
            self.coast = self.ax.coastlines('50m')
        else:
            met_mods[self.metVar.get()].setup_ax(self)
            met_mods[self.metVar.get()].update_plot(self)
            
        # Add airports and FIR boundaries
        self.draw_airports()
                
        # Check the toggles and turn off displays if needed
        for key in ['grid', 'coast', 'image']:
           if not self.toggles[key].get():
              print('SETUP_AX: Turning off {}'.format(key))
              getattr(self, 'toggle_'+key)()
            
        # Initiate flight route objects
        self.line = LineCollection(np.zeros([1, 2, 2]),
                                   transform=ccrs.Geodetic(), animated=True,
                                   pickradius=10)
        self.ax.add_collection(self.line)
        self.wline = LineCollection(np.zeros([1, 2, 2]),
                                    transform=ccrs.Geodetic(), animated=True,
                                    colors='w', linewidths=3, pickradius=10)
        self.ax.add_collection(self.wline)
        self.dots = self.ax.scatter([], [], c='r', animated=True,
                                    edgecolors='k',
                                    transform=ccrs.PlateCarree())
        self.anns = []    # there's no AnnotationCollection, so just use a list

        # Timeseries ax
        self.tsax = self.fig.add_axes(self.layout['tsax'])
        self.tsax.grid()
        self.tsline = LineCollection(np.zeros([1, 2, 2]), animated=True,
                                     pickradius=10)
        self.tsax.add_collection(self.tsline)
        self.tsdots = self.tsax.plot([], [], marker='o', markerfacecolor='r',
                                     linestyle='None', animated=True)[0]
        self.tsanns = []

        self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)

        # Radio buttons for selecting variable in timeseries plot
        self.tsxvarax = self.fig.add_axes(self.layout['tsxvarbn'])
        self.tsxvarbn = RadioButtons(
            self.tsxvarax, ['Dist [nm]', 'Time [hr]', 'Lons', 'Lats'])
        self.tsxvarbn.on_clicked(self.set_tsvars)
        self.set_tsvars('Dist [nm]', init=True)

        # Connect events to canvas
        self.fig.canvas.mpl_connect('button_press_event',
                                    self.fig_button_press_callback)
        self.fig.canvas.mpl_connect('draw_event',
                                    self.fig_draw_callback)
        self.fig.canvas.mpl_connect('scroll_event',
                                    self.fig_scroll_callback)
        self.set_default_filename()
        
    def draw_airports(self):
        if hasattr(self, 'airport_objects'):
            for ao in self.airport_objects: ao.remove()
        bbox = dict(boxstyle="round", ec='none', fc="w", alpha=0.5)
        pc = ccrs.PlateCarree()
        pctransform = pc._as_mpl_transform(self.ax)
        ao = [] # store airport objects for toggling
        self.airport_objects = ao
        for name, pt in airports.items():
            ao.append(self.ax.plot(pt[0], pt[1], 'lightcoral', marker='o',
                                   transform=pc)[0])
            ao.append(self.ax.annotate(name, [pt[0], pt[1]], va='center',
                                       xycoords=pctransform, color='lightcoral',
                                       annotation_clip=True, bbox=bbox,
                                       xytext=[5, 0],
                                       textcoords='offset points'))
            if name in airport_isochrones:
                for h, lab in zip(*airport_isochrones[name]):
                    r = h * self.flightdef.legtype_spds['transit']
                    n = 180
                    circle_points = cgeodesic.Geodesic().circle(
                        lon=pt[0], lat=pt[1], radius=nm2km(r)*1000,
                        n_samples=n, endpoint=False)
                    geom = shapely.geometry.Polygon(circle_points)
                    ao.append(self.ax.add_geometries((geom,), crs=pc,
                                                     facecolor='none',
                                                     edgecolor='lightcoral'))
                    for i in range(0, 12, 2):
                        ci = int(np.round(i * n / 12))
                        ao.append(self.ax.annotate(
                            lab, [circle_points[ci][0], circle_points[ci][1]],
                            va='center', ha='center', xycoords=pctransform,
                            color='lightcoral', annotation_clip=True,
                            bbox=bbox, xytext=[0, 0],
                            textcoords='offset points'))
        for name, (pts, col) in fir_boundaries.items():
            lons = np.array([pt[0] for pt in pts])
            lats = np.array([pt[1] for pt in pts])
            ao.append(self.ax.plot(lons, lats, color=col, transform=pc)[0])
            labi = np.argmax(lats-lons) # Most NW point
            ao.append(self.ax.annotate(
                name, [lons[labi], lats[labi]], va='top', ha='left',
                xycoords=pctransform, color=col, annotation_clip=True, bbox=bbox,
                xytext=[5, -5], textcoords='offset points'))
        if not self.toggles['airports'].get():
            print('SETUP_AX: Turning off airports')
            self.toggle_airports()


    def set_tsvars(self, label=None, init=False):
        if label == 'Dist [nm]' or 'tsxvals' not in dir(self):
            self.tsax.set_xlim(0, 500)
            self.tsax.set_xlabel('Distance [nm]')
        if label == 'Time [hr]':
            self.tsax.set_xlim(0, 10)
            self.tsax.set_xlabel('Time [hr]')
        if label == 'Lons':
            self.tsax.set_xlim(-10, 30)
            self.tsax.set_xlabel('Longitude')
        if label == 'Lats':
            self.tsax.set_xlim(70, 85)
            self.tsax.set_xlabel('Latitude')
        self.tsax.set_ylim(0, 6000)
        self.tsax.set_ylabel('Alt [ft]')
        self.fig.canvas.draw_idle()
        if init is not True: self.update_fig()

    def update_flightdef(self, event=None):
        """Read flightdef from info panel and update display"""
        if debug: print('update_flightdef')
        self.flightdef.name = self.nameVar.get()
        self.flightdef.aircraft = self.aircraftVar.get()
        self.flightdef.legtype_spds = legtype_spds[self.aircraftVar.get()]
        self.draw_airports()
        s = self.flightdefST.get(0.0, tk.END).strip().strip('\n')
        if len(s) > 0:
            self.flightdef.waypoints = [WayPoint_from_repr(line)
                                        for line in s.split('\n')]
        else:
            self.flightdef.waypoints = []
        self.update_display()
        self.set_default_filename()

    def print_flightdef(self, event=None):
        """Print flightdef to stdout"""
        if debug: print('print_flightdef')
        print('\nCURRENT FLIGHTDEF:\n------------------')
        print(self.flightdef)

    def clear_flightdef(self, event=None):
        """Clear flightdef waypoints and update display"""
        if debug: print('clear_flightdef')
        self.flightdef.waypoints = []
        self.update_display()
        self.set_tsvars()
    
    def relabel_waypoints(self):
        """Relabel waypoints as consecutive letters plus airports"""
        if debug: print('relabel_waypoints')
        i = 0
        labs = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        for wpi, wp in enumerate(self.flightdef.waypoints):
            near_airport = is_near_airport(wp, wplock=wplock)
            near_prev = is_near_other_waypoints(
                wp, self.flightdef.waypoints[:wpi], wplock=wplock/100)
            if near_airport is not None:
                wp.name = near_airport
            elif near_prev is not None:
                wp.name = self.flightdef.waypoints[near_prev].name
            else:
                wp.name = labs[i] + self.flightdef.name
                i = i + 1
        self.update_display()

    def update_display(self):
        """Update display to show current flightdef."""
        if debug: print('update_dislpay')
        self.update_info()
        self.update_fig()

    def update_info(self):
        """Update info panel to show current flightdef"""
        if debug: print('update_info')
        self.nameVar.set(self.flightdef.name)
        self.aircraftVar.set(self.flightdef.aircraft)
        self.flightdefST.delete(0.0, tk.END)
        self.flightdefST.insert(
            0.0, '\n'.join([wp.__repr__() for wp in self.flightdef.waypoints]))
        self.summaryLabel.configure(text=self.flightdef.total_summary())
        #self.legtypeLabel.configure(text=self.flightdef.print_speeds())

    def update_fig(self):
        """Update fig to show current flightdef"""
        if debug: print('update_fig')
        self.update_lines()
        self.fig.canvas.restore_region(self.background)
        self.ax.draw_artist(self.line)
        self.ax.draw_artist(self.wline)
        self.ax.draw_artist(self.dots)
        for ann in self.anns: self.ax.draw_artist(ann)
        self.fig.canvas.blit(self.ax.bbox)    
        self.tsax.draw_artist(self.tsline)
        self.tsax.draw_artist(self.tsdots)
        for ann in self.tsanns: self.tsax.draw_artist(ann)
        self.fig.canvas.blit(self.tsax.bbox)

    def update_lines(self):
        """Update line objects with current flightdef"""
        if debug: print('update lines')
        self.line.set_paths(self.flightdef.leg_segments())
        self.line.set_color([legtype_cols[leg[0].legtype]
                             for leg in self.flightdef.legs()])
        self.wline.set_paths(self.flightdef.leg_segments())
        for ann in self.anns: ann.remove()
        self.anns[:] = []
        for wp in self.flightdef.waypoints:
            self.anns.append(self.annotate_wp(wp))
        self.dots.set_offsets(
            np.array([self.flightdef.lons(), self.flightdef.lats()]).T)
        if self.tsxvarbn.value_selected == 'Dist [nm]':
            xvals = np.insert(km2nm(
                self.flightdef.total_dist(cumulative=True)), 0, 0)
        elif self.tsxvarbn.value_selected == 'Time [hr]':
            xvals = np.insert(self.flightdef.total_time(cumulative=True), 0, 0)
        elif self.tsxvarbn.value_selected == 'Lons':
            xvals = self.flightdef.lons()
        elif self.tsxvarbn.value_selected == 'Lats':
            xvals = self.flightdef.lats()
        yvals = self.flightdef.alts()
        tssegments = [((x0, y0), (x1, y1)) for x0, y0, x1, y1 in
                  zip(xvals[:-1], yvals[:-1], xvals[1:], yvals[1:])]
        self.tsline.set_paths(tssegments)
        self.tsline.set_color([legtype_cols[leg[0].legtype]
                               for leg in self.flightdef.legs()])
        
        for ann in self.tsanns: ann.remove()
        self.tsanns[:] = []
        for i, wp in enumerate(self.flightdef.waypoints):
            self.tsanns.append(self.tsax.annotate(
                wp.name[0], [xvals[i], yvals[i]], clip_on=True,
                animated=True, xytext=[2, 2], textcoords='offset points'))
        
        self.fig.canvas.draw_idle()
        self.tsdots.set_xdata(xvals)
        self.tsdots.set_ydata(yvals)
        self.tsax.relim()
        self.tsax.autoscale()
        self.tsax.draw(renderer=self.fig.canvas.renderer)
        self.tsxvals = xvals
        self.tsyvals = yvals
        # so the wp labels can be seen:
        ymin, ymax = self.tsax.get_ylim()
        self.tsax.set_ylim(ymin, ymax+((ymax-ymin)*0.35))

    def set_default_filename(self):
        """Set the default filename for the matplotlib save image button"""
        mpl.rcParams['savefig.directory'] = self.flightdef.fddir
        fn = self.flightdef.name + '_' + self.metVar.get()
        for k, MetVar in self.MetVars[self.metVar.get()].items():
            v = MetVar.get()
            if type(v) == datetime.datetime:
                fn += '_' + v.strftime(datefmt)
            else:
                fn += '_' + v
        fn += '.png'
        if debug: print('set_default_filename: ', fn)
        self.canvas.get_default_filename = \
            lambda: fn
        
    def annotate_wp(self, wp):
        """Annotate WayPoint wp on map ax.
        Note: cartopy projections don't work for annotate transform keyword,
        so need to construct the mpl transform instead."""
        transform = ccrs.PlateCarree()._as_mpl_transform(self.ax)
        return self.ax.annotate(wp.name[0], [wp.lon, wp.lat], clip_on=True,
                                xycoords=transform, animated=True,
                                xytext=[2, 2], textcoords='offset points')
            
    def fig_button_press_callback(self, event):
        """Called whenever a mouse button is pressed."""
        if self.ax.get_navigate_mode():
            # Don't do anything if any figure navigation widgets selected
            if debug: print('passing fig_button_press_callback')
            return
        # Get name ready for any new waypoint
        near_airport = [is_near_airport(wp, wplock=wplock) is not None
                        for wp in self.flightdef.waypoints]
        npts = len(self.flightdef.waypoints) - np.sum(near_airport, dtype=int)
        new_wpname = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'[npts] + self.flightdef.name
        if event.inaxes == self.ax:
            lcontains, linfo = self.line.contains(event)
            dcontains, dinfo = self.dots.contains(event)
            lon, lat = self.dataxy_to_lonlat(event.xdata, event.ydata)
            if dcontains:
                i = dinfo['ind'][-1]
                if event.button == 1:              # Append destination airport
                    if is_near_airport(
                            self.flightdef.waypoints[i], wplock=wplock):
                        alt = self.flightdef.waypoints[-1].alt
                        legtype = self.flightdef.waypoints[-1].legtype
                        wp = locked_WayPoint(
                            lon, lat, alt, name=new_wpname, legtype=legtype,
                            wplock=wplock)
                        self.flightdef.waypoints.append(wp)
                    else:
                        self.start_drag(i)         # Drag waypoint
                elif event.button == 3:            # Delete waypoint
                    self.flightdef.waypoints.pop(i)
            elif event.button == 1:                # Append waypoint
                if new_wpname[0] == 'A':
                    alt = 1000.0
                    legtype = 'transit'
                else:
                    alt = self.flightdef.waypoints[-1].alt
                    legtype = self.flightdef.waypoints[-1].legtype
                wp = locked_WayPoint(
                    lon, lat, alt, name=new_wpname, legtype=legtype,
                    wplock=wplock)
                self.flightdef.waypoints.append(wp)
            elif lcontains:
                if event.button == 2:               # Insert waypoint
                    prevlegi = linfo['ind'][0]
                    alt = self.flightdef.waypoints[prevlegi].alt
                    legtype = self.flightdef.waypoints[prevlegi].legtype
                    wp = locked_WayPoint(
                        lon, lat, alt, name=new_wpname,
                        legtype=legtype, wplock=wplock)
                    self.flightdef.waypoints.insert(prevlegi+1, wp)
        elif event.inaxes == self.tsax:
            lcontains, linfo = self.tsline.contains(event)
            dcontains, dinfo = self.tsdots.contains(event)
            if dcontains:
                i = dinfo['ind'][0]
                if event.button == 1:               # Drag waypoint
                    self.start_ts_drag(i)
                elif event.button == 3:             # Delete waypoint
                    self.flightdef.waypoints.pop(i)
            elif lcontains:
                i = linfo['ind'][0]
                if event.button == 2:               # Insert waypoint
                    lon = self._interp(i, event.xdata, self.tsxvals,
                                       self.flightdef.lons())
                    lat = self._interp(i, event.xdata, self.tsxvals,
                                       self.flightdef.lats())
                    alt = event.ydata
                    wp = locked_WayPoint(
                        lon, lat, alt, name=new_wpname, wplock=wplock)
                    self.flightdef.waypoints.insert(i+1, wp)
            
        else:
            return
        self.update_display()
        
    def fig_scroll_callback(self, event, base_scale=1.05):
        if debug: print('fig_scroll_callback')
        if event.inaxes != self.ax: return
        # get the current x and y limits
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        x = event.xdata # get event x location
        y = event.ydata # get event y location
        if event.button == 'up': scale_factor = 1/base_scale
        elif event.button == 'down': scale_factor = base_scale
        self.ax.set_xlim([x - (x - x0) * scale_factor,
                          x + (x1 - x) * scale_factor])
        self.ax.set_ylim([y - (y - y0) * scale_factor,
                          y + (y1 - y) * scale_factor])
        self.update_fig()

    def _interp(self, i, newx, xarr, yarr):
        frac = (newx - xarr[i]) / (xarr[i+1] - xarr[i])
        return yarr[i] + frac * (yarr[i+1] - yarr[i])

    def fig_draw_callback(self, event=None):
        if debug: print('fig_draw_callback')
        self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        self.ax.draw_artist(self.wline)
        self.ax.draw_artist(self.line)
        self.ax.draw_artist(self.dots)
        for ann in self.anns: self.ax.draw_artist(ann)
        self.tsax.draw_artist(self.tsline)
        self.tsax.draw_artist(self.tsdots)
        for ann in self.tsanns: self.tsax.draw_artist(ann)
        #self.update_fig()   # Not needed?

    def start_drag(self, i):
        self.drag_i = i
        cid1 = self.fig.canvas.mpl_connect('motion_notify_event',
                                           self.drag_update)
        cid2 = self.fig.canvas.mpl_connect('button_release_event',
                                           self.end_drag)
        self.drag_cids = [cid1, cid2]
        self.update_display()

    def drag_update(self, event):
        if event.xdata != None and event.ydata != None:
            xmin, xmax = self.ax.get_xlim()
            ymin, ymax = self.ax.get_ylim()
            if ymin < event.ydata < ymax and xmin < event.xdata < xmax:
                lon, lat = self.dataxy_to_lonlat(event.xdata, event.ydata)
        else:
            return
        # Lock to nearby points
        if wplock is not None:
            for pt in [wp.pt() for i, wp in enumerate(self.flightdef.waypoints)
                       if i != self.drag_i]:
                dist = greatcircle((lon, lat), (pt[0], pt[1]))
                if dist < wplock: lon, lat = pt
        wp = locked_WayPoint(
            lon, lat, alt=self.flightdef.waypoints[self.drag_i].alt,
            name=self.flightdef.waypoints[self.drag_i].name,
            desc=self.flightdef.waypoints[self.drag_i].desc,
            legtype=self.flightdef.waypoints[self.drag_i].legtype,
            wplock=wplock)
        self.flightdef.waypoints[self.drag_i] = wp
        self.update_display()

    def end_drag(self, event):
        for cid in self.drag_cids:
            self.fig.canvas.mpl_disconnect(cid)
        self.drag_cids = []

    def start_ts_drag(self, i):
        self.drag_i = i
        cid1 = self.fig.canvas.mpl_connect('motion_notify_event',
                                           self.ts_drag_update)
        cid2 = self.fig.canvas.mpl_connect('button_release_event',
                                           self.end_ts_drag)
        self.drag_cids = [cid1, cid2]

    def ts_drag_update(self, event):
        def round_alts(val, base=10):
            return base * round(float(val) / base)
        
        if event.ydata != None:
            ymin, ymax = self.tsax.get_ylim()
            if ymin < event.ydata < ymax:
                lon, lat = self.flightdef.waypoints[self.drag_i].pt()
                wp = locked_WayPoint(
                    lon, lat, round_alts(event.ydata),
                    name=self.flightdef.waypoints[self.drag_i].name,
                    desc=self.flightdef.waypoints[self.drag_i].desc,
                    legtype=self.flightdef.waypoints[self.drag_i].legtype,
                    wplock=wplock)
                self.flightdef.waypoints[self.drag_i] = wp
                self.update_display()

    def end_ts_drag(self, event):
        for cid in self.drag_cids:
            self.fig.canvas.mpl_disconnect(cid)
        self.drag_cids = []

    def dataxy_to_lonlat(self, xs, ys):
        if type(xs) != np.ndarray:
            return ccrs.PlateCarree().transform_point(
                xs, ys, self.ax.projection)
        else:
            lonlatarray = ccrs.PlateCarree().transform_points(
                self.ax.projection, xs, ys)
            return lonlatarray[:, 0], lonlatarray[:, 1]

    def lonlat_to_dataxy(self, lons, lats):
        if type(lons) != np.ndarray:
            return self.ax.projection.transform_point(
                lons, lats, ccrs.PlateCarree())
        else:
            xyarray = self.ax.projection.transform_points(
                ccrs.PlateCarree(), lons, lats)
            return xyarray[:, 0], xyarray[:, 1]

    def save(self, event=None):
        """Called from save button"""
        fn = filedialog.asksaveasfilename(defaultextension=".dat",
                                          initialdir=self.flightdef.fddir,
                                          initialfile=self.flightdef.name,
                                          filetypes = [('.dat', '*.dat')])
        self.flightdef.savedat(fn)
        self.flightdef.savetxt(fn.split('.')[0] + '.txt')
        self.flightdef.savecsv(fn.split('.')[0] + '.csv')
        self.flightdef.savegpx(fn.split('.')[0] + '.gpx')
        # Save current image and include in doc
        fnfig = fn.split('.')[0] + '_fig_for_sortie.png'
        print('\nSAVE: Saving current figure for use in savedoc: {}'.\
              format(fnfig))
        self.fig.savefig(fnfig, dpi=200)
        self.flightdef.savedoc(fn.split('.')[0] + '_sortie.docx', fnfig)
        
    def load(self, event=None):
        """Called from load button"""
        fn = filedialog.askopenfilename(
            title = "Select a File", filetypes = [("FlightDefs", "*.dat *.gpx")],
            initialdir=self.flightdef.fddir)
        if fn[-3:] == 'dat': self.flightdef = loaddat(fn)
        if fn[-3:] == 'gpx': self.flightdef = loadgpx(fn)
        self.update_display()
        self.set_default_filename()
        
    def windy(self, event=None):
        """Open Windy.com with this flight def loaded into route planner"""
        coordstr = ';'.join(['{}, {}'.format(wp.lat, wp.lon)
                             for wp in self.flightdef.waypoints])
        url = 'https://www.windy.com/distance/car' + coordstr
        webbrowser.open_new(url)
        
    def help(self, event=None):
        messagebox.showinfo(
            title='Instructions',
            message=\
            'Edit WayPoints by clicking on map:\n'\
            '    LEFT = append\n'\
            '    MIDDLE = insert\n'\
            '    RIGHT = delete\n'\
            '    DRAG = move\n'\
            'Or, edit text and select \'Update FlightDef\'. Format:\n'\
            '    Name, Lon, Lat, Alt [ft], legtype, description'
            )

def main():
    print('Running the flight Planner!')
    p = PlannerGUI()
    p.mainloop()

if __name__ == '__main__':
    main()
