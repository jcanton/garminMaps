#!/usr/bin/env python3

from garminconnect import Garmin
import pandas as pd
import folium
from folium import plugins as fplugins
import configparser
from datetime import date, datetime
import os, socket
import logging
import gmFunctions as gmf

#===============================================================================
# Data and config
#
config = configparser.ConfigParser()
config.read(os.path.join(os.path.expanduser('~'), '.python-github.cfg'))
GARMIN_ID = config.get('garmin.maps', 'GARMIN_ID')
GARMIN_PW = config.get('garmin.maps', 'GARMIN_PW')
GARMIN_AC = config.get('garmin.maps', 'GARMIN_ACTIVITIES')

today     = date.today()
dateStart = date(2021, 1, 1)
dateEnd   = today
dateFmt   = '%Y-%m-%d'

gpxDir = 'gpxFiles'
mapDir = 'maps'
activityTypes = GARMIN_AC.strip().replace(' ', '').split(',')
#activityTypes = ['walking'] # TODO remove after debugging

#===============================================================================
# Initialize logger
#
logging.basicConfig(filename='log_maps.log',
                    level=logging.INFO,
                    format='%(message)s',
                    filemode='w')

logging.info('============= start mapping =============')
logging.info('Host: ' + socket.gethostname())
logging.info('Date: ' + datetime.now().strftime('%Y-%m-%d %H:%M'))

#===============================================================================
# Init Garmin client
#
client = Garmin(GARMIN_ID, GARMIN_PW)
client.login()
fullName   = client.get_full_name()
unitSystem = client.get_unit_system()
todayStats = client.get_stats(today.isoformat()) # TODO unused for now

logging.info('Garmin user: ' + fullName)
logging.info('Unit system: ' + unitSystem)

#===============================================================================
# Get activities
#
logging.info('Selected activities: ' + ', '.join(activityTypes))
logging.info('')
for activityType in activityTypes:

    logging.info('\tDownloading activities: ' + activityType)

    outputDir = os.path.join(gpxDir, activityType)
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)
    
    activities = client.get_activities_by_date(dateStart.strftime(dateFmt), dateEnd.strftime(dateFmt), activityType)
    
    for activity in activities:
    
        activity_id    = activity['activityId']
        activity_start = datetime.strptime(activity['startTimeLocal'], '%Y-%m-%d %H:%M:%S')
    
        output_file = os.path.join(outputDir, '{0:s}.gpx'.format(activity_start.strftime('%Y%m%d_%H%M%S')))
    
        if not os.path.isfile(output_file):
            gpx_data = client.download_activity(activity_id, dl_fmt=client.ActivityDownloadFormat.GPX)
            with open(output_file, 'wb') as fb:
                fb.write(gpx_data)

#===============================================================================
# Build maps
#
logging.info('')
for activityType in activityTypes:

    logging.info('\tBuilding map for: ' + activityType)

    # generate map
    fmap = folium.Map(
            tiles=None,
            location=[47.34967, 8.53660],
            zoom_start=13,
            control_scale=True,
            prefer_canvas=True,
            )
    folium.TileLayer('OpenStreetMap'      ).add_to(fmap)
    folium.TileLayer('Stamen Terrain'     ).add_to(fmap)
    folium.TileLayer('Stamen Toner'       ).add_to(fmap)
    folium.TileLayer('CartoDB dark_matter').add_to(fmap)
    fplugins.Fullscreen(
            position='topright',
            title='Fullscreen',
            title_cancel='Exit Fullscreen',
            force_separate_button=True,
            ).add_to(fmap)
    heatMapData = pd.DataFrame([])

    # load gpx files and add tracks to map
    fg = folium.FeatureGroup(name='GPX tracks', show=True)
    fmap.add_child(fg)
    inputDir = os.path.join(gpxDir, activityType)
    gpxFiles = os.listdir(inputDir)
    for gpxFile in gpxFiles:
        gpx_df, gpx_points = gmf.gpxParse(os.path.join(inputDir, gpxFile))
        # add data to heatMapData
        heatMapData = heatMapData.append(gpx_df)
        #
        # add gpx track to map
        tooltip = folium.Tooltip(text='')
        popup = folium.Popup(html_camino_start, max_width=400)
        folium.PolyLine(
                gpx_points,
                tooltip=tooltip,
                popup=popup,
                color='blue',
                weight=4.0,
                opacity=.5
                ).add_to(fmap).add_to(fg)

    fplugins.HeatMap(
            data=heatMapData[['Latitude', 'Longitude']],
            name='Heat map',
            radius=8,
            max_zoom=13,
            show=False,
            ).add_to(fmap)

    fmap.add_child(folium.LayerControl())

    # save map
    outputDir = mapDir
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    fmap.save(os.path.join(mapDir, 'map_{0:s}.html'.format(activityType)))
