"""
Useful functions that are used by all of the XX_images.py files.
"""

import os, sys
import numpy as np
from datetime import datetime
import threading
import tkinter as tk
from tkinter import ttk


def set_plotdir(datapath, tag):
    """Set directory for saving plots."""
    plotdir = os.path.join(datapath, 'data', tag+'_images')
    print('Setting {} plot directory: {}'.format(tag.upper(), plotdir))
    if not os.path.exists(plotdir):
        os.makedirs(plotdir, exist_ok=True)
    return plotdir
    
    
def today():
    """Get datetime for 00Z today."""
    now = datetime.today()
    return datetime(now.year, now.month, now.day)


def makeform(root, d):
    """Create a simple form in a tk window root.
    
    d is a dictionary holding: {'form text': initial value}
    """
    entries = {}
    for k, v in d.items():
        row = tk.Frame(root)
        lab = tk.Label(row, width=22, text=k + ": ", anchor='w')
        ent = tk.Entry(row)
        val = v if type(v)==str else v.get()
        ent.insert(0, val)
        row.pack(side=tk.TOP, fill=tk.X, padx=5 , pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        entries[k] = ent
    return entries


def harvest_gui(d, text, harvest_fn):
    """General function for creating a form for harvesting images from the web.
    
    Submit button uses threading so can keep interacting with the GUI whilst
    the retrievals are running.
    
    d: Dictionary of the form {'form text': initial value}.
    text: Instructions to display on form.
    harvest_fn: A function which accepts the key-value pairs in d.
    """
    def _submitform(entries):            
        def worker(entries, stop, finish):
            harvest_fn(*[entry.get() for k, entry in entries.items()],
                       stop, finish)
        stop_retrieve[0] = False
        #b1['state'] = 'disabled'
        args = (entries, lambda: stop_retrieve[0], _finishretrieve)
        t = threading.Thread(target=worker, args=args)
        t.start()
        
    def _stopretrieve():
        print('\nStopping retrieval...')
        stop_retrieve[0] = True
        #b1['state'] = 'normal'
        
    def _finishretrieve():
        #b1['state'] = 'normal'
        return
    
    root = tk.Tk()
    root.title('Image Harvester')
    tk.Label(root, text=text, padx=5, pady=5).pack(side=tk.TOP)
    ents = makeform(root, d)
    stop_retrieve = [False]
    b1 = ttk.Button(root, text='Submit', command=lambda e=ents: _submitform(e))
    b2 = ttk.Button(root, text='Stop', command=lambda: _stopretrieve())
    b1.pack(side=tk.LEFT, padx=5, pady=5)
    b2.pack(side=tk.LEFT, padx=5, pady=5)
    root.mainloop()
    

def contiguous_regions(condition):
    """
    Finds contiguous True regions of a 1d boolean array.
    
    Returns 3 1d arrays: start indicies, stop indicies and lengths of regions.
    """
    idx, = np.diff(condition).nonzero()
    idx += 1 # need to shift indices because of diff
    if condition[0]: idx = np.r_[0, idx]
    if condition[-1]: idx = np.r_[idx, condition.size] # Edit
    starts = idx[0::2]
    stops = idx[1::2]
    lengths = stops - starts
    return starts, stops, lengths

# def cutout_map(im, white_thres=0.95, frac_thres=0.7, colbar=False):
#     """
#     Cutout an image array im[rows, cols, :] to those rows and cols which are
#     not predominatnetly white.
#     """
#     im0 = np.min(im, axis=2)
#     # Get largest contiguous region of rows with lots of non-white pixels
#     rows = np.mean(im0 > white_thres, axis=1) < frac_thres
#     starts, stops, lengths = contiguous_regions(rows)
#     for i, length in enumerate(lengths):
#         if length < np.max(lengths): rows[starts[i]:stops[i]]=False
#     # Repeat for columns
#     cols = np.mean(im0 > white_thres, axis=0) < frac_thres
#     starts, stops, lengths = contiguous_regions(cols)
#     for i, length in enumerate(lengths):
#         if length < np.max(lengths): cols[starts[i]:stops[i]]=False
#     # To get colourbar, just return all rows after the contiguous region instead
#     if colbar:
#         starts, stops, lengths = contiguous_regions(rows)
#         rows[starts[0]:stops[0]] = False
#         rows[stops[0]:] = True
#     print('CUTOUT_MAP: Input shape = {}'.format(im.shape))
#     im = im[rows]
#     im = im[:, cols]
#     print('CUTOUT_MAP: Output shape = {}'.format(im.shape))
#     return im


# def cutout_map(im, get_colbar=False):
#     """
#     Trying out new cutout method
#     """
#     # Get mean darkness of each row and column
#     # Lower values = dark
#     im0 = np.max(im[:, :, :3], axis=2)
#     rowmeans = np.mean(im0, axis=1)
#     colmeans = np.mean(im0, axis=0)
    
#     # Locate the darkest two rows/cols
#     rowinds = rowmeans.argsort()[:4]
#     colinds = colmeans.argsort()[:2]
    
#     # Fix for wide colorbars: get smallest indices in search
#     rowinds = rowinds[rowinds.argsort()[:2]]
#     colinds = colinds[colinds.argsort()[:2]]
    
#     rows = slice(rowinds[1], None) if get_colbar else slice(*rowinds)
#     cols = slice(*colinds)
#     return im[rows, cols]


def cutout_map(im, get_colbar=False, white_thres=0.999):
    """
    Trying out new cutout method.
    
    white_thres allows for axis ticks in ssh images
    """
    # Get biggest contiguous range of rows that are not all white
    # ('all white' means the row mean the minimum rbg value is >= white_thres)
    im0 = np.min(im[:, :, :3], axis=2)
    rowmeans = np.mean(im0, axis=1)
    starts, stops, lengths = contiguous_regions(rowmeans < white_thres)
    irow = np.argmax(lengths)
    if get_colbar is False:
        rows = slice(starts[irow], stops[irow])
    else:
        rows = slice(stops[irow], None)
        
    # Subset to these rows and repeat for columns
    im0 = im0[rows]
    colmeans = np.mean(im0, axis=0)
    starts, stops, lengths = contiguous_regions(colmeans < white_thres)
    icol = np.argmax(lengths)
    cols = slice(starts[icol], stops[icol])

    return im[rows, cols]