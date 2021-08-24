# Garmin maps

This is a python package for automatically generating beautiful
leaflet maps with your own gpx tracks recorded on a Garmin device.
In order to use this script you should have an account on [Garmin
Connect](https://connect.garmin.com/) with a few activities recorded.

![Walking map](https://jacopocanton.com/assets/images/walkingMap.gif)

You can view an interactive example on my website at
[jacopocanton.com/maps](https://jacopocanton.com/maps/) and read about how this
script works in my blog post:
[jacopocanton.com/blog/garminMaps](https://jacopocanton.com/blog/garminMaps/).

## Requirements

The script is tested with python 3.8 and requires the following
packages:

```[bash]
pip3 install pandas garminconnect gpxpy folium
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

In this file you can safely store your credentials (as they will reside only on
your hard drive), select one or more activity you want to create maps for (in a
comma separated list), and select a start date for downloading the gpx tracks
(the end date defaults to the time the script is run).

### Running the script

Running the script is as simple as `python3 main.py`.

The script downloads your gpx tracks in the `gpxFiles/` directory, the maps are
saved as html files in `maps/`, and log messages are stored in the logfile
`log_msg.log`.

You can then embed the html files directly on your website!
Read my blog post to find out how:
[jacopocanton.com/blog/garminMaps](https://jacopocanton.com/blog/garminMaps/).
