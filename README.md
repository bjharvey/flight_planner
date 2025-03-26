# Flight Planner

Flight planner GUI for interactive click-and-drag flight planning.

## Features

- **Design flight tracks**: Add, move and edit waypoints on a map.
- **Overlay Forecast Images**: Download and overlay forecast charts from several sources.
- **Export flight track**: Save flight track as CSV, GPX, and a formatted sortie brief.
- **Load into Windy.com**: Load the flight track directly into Windy.com.

## Installation

Clone the repository:
```
git clone https://github.com/bjharvey/flight_planner.git
```

## Running

### Option 1

Run the application:
```
cd flight_planner
python -m flight_planner.gui
```
This allows for quick and easy tweaking of the code.

It requires correct packages to be installed, which can be checked with
```
pip install -r requirements.txt
```

### Option 2

Alternatively, install the application:
```
cd flight_planner
python setup.py install
flight_planner
```
This installs a fixed version of the code in your site-packages directory
which can be run from the command line. It also  checks for and installs
all required dependencies.

To uninstall:
```
pip uninstall flight_planner
```

### Updating

To check if your version is up to date:
```
git fetch
git status -uno
```

And to update it if it's not:
```
git pull origin main
```

## Basic Usage Instructions

1. On start up, select a save location *SAVE_DIR*. A subdirectory *data* is created for all outputs.
2. To plan a flight:
    - Edit WayPoints by clicking on the map:
        - LEFT = Append new WayPoint
        - MIDDLE = Insert new WayPoint (if near an existing leg)
        - RIGHT = Delete (if near an existing WayPoint)
        - DRAG = Move WayPoint
    - Or, edit the text box directly and select *Update FlightDef*:
        - Format for each WayPoint: Name, Longitude, Latitude, Altitude, LegType, Description [optional]
        - Longitude/Latitude are in decimal degrees, Altitude is in feet
        - LegType determines the speed and must be one of the options listed after *Summary*
3. To save a flight definition, click *Save*. This creates several files in *SAVE_DIR/flight_defs* including:
    - a *.dat* file holding the basic info (for reloading into flight_planner)
    - a *.gpx* file which can be imported into pilot's software, and windy.com
    - a *.docx* file holding a partially completed sortie brief
4. To reload a saved flight definition, click *Load* and select either:
    - a *.dat* file produced by flight_planner
    - a *.gpx* file, e.g. produced by windy.com
5. To overlay forecast images:
    - Select *Met Image*
    - Select *Retrieve* to download new images. This opens a new GUI for selecting model/domain/times etc (and entering credentials) and submitting the retrieval. Note: the retrieval simply attempts to download images matching the settings and will just fail if they can't be found. See terminal output for details. The files are saved in *SAVE_DIR/mo_images*.
    - Select *Webpage* to open the source webpage (e.g. to check what is available)

### User configuration file

Campaign specific customisations can be made in `user_config.py`, including:
- The map projection used and its extent on start up
- Aircrafts and speeds/leg types
- Map annotations e.g. airports and FIR boundaries
- Sources of met images (including details of map projections and extents for each domain)

Each source of met images has a `images_xxx.py` file which deals with downloading and displaying the relevant images. To add a new source, copy `images_mo.py` and adapt the functions to the new source.   

### Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For questions or support, please contact ben.harvey@ncas.ac.uk.