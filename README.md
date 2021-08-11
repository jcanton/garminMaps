# Garmin maps

This is a python package for automatically generating beautiful
leaflet maps with gpx tracks.

## Requirements

The script is tested with python 3.8 and requires the following
packages:

```[bash]
pip install pandas garminconnect gpxpy folium
```

## Usage

Before running, you should write a `.python-github.cfg` configuration
file as in the example below and place it in your home directory:

```[bash]
[garmin.maps]
GARMIN_ID = your_garmin_username
GARMIN_PW = your_garmin_account_password
GARMIN_ACTIVITIES = walking, running, cycling, hiking
GARMIN_DATESTART = 2021-01-01
```

In this file you can safely store your credentials, select the individual
activities you want to create maps for, and select a start date for downloading
the gpx tracks.

Running the script is as simple as `python main.py`.

The gpx tracks are downloaded in the `gpxFiles/` directory, the maps are saved
as html files in `maps/`, and log messages are stored in the logfile
`log_msg.log`.
