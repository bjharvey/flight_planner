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

## Usage

### Option 1
Run the application:
```
cd flight_planner
python flight_planner.py
```
This allows for quick and easy tweaking of the code.
It requires correct packages to be installed, which can be checked with
```
pip install -r requirements.txt
```

### Option 2:
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

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For questions or support, please contact ben.harvey@ncas.ac.uk.