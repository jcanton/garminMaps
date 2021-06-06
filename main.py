#!/usr/bin/env python3

from garminconnect import Garmin
import pandas as pd
import folium
from folium import plugins as fplugins
import configparser
from datetime import date, datetime, timedelta
from dateutil import tz
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

logging.info('Done')
logging.info('')

#===============================================================================
# Build maps
#
for activityType in activityTypes:

    logging.info('\tBuilding map for: ' + activityType)

    # generate map
    fmap = folium.Map(
            tiles=None,
            location=[47.34967, 8.53660],
            zoom_start=14,
            control_scale=True,
            prefer_canvas=True,
            )
    folium.TileLayer('Stamen Terrain',      name='Stamen Terrain'     ).add_to(fmap)
    folium.TileLayer('Stamen Toner',        name='Stamen Toner'       ).add_to(fmap)
    folium.TileLayer('CartoDB dark_matter', name='CartoDB dark matter').add_to(fmap)
    folium.TileLayer('OpenStreetMap',       name='OpenStreet Map'     ).add_to(fmap)
    fplugins.Fullscreen(
            position='topright',
            title='Fullscreen',
            title_cancel='Exit Fullscreen',
            force_separate_button=True,
            ).add_to(fmap)
    heatMapData = pd.DataFrame([])

    # load gpx files and add tracks to map
    inputDir = os.path.join(gpxDir, activityType)
    gpxFiles = os.listdir(inputDir)
    # create a new python dict to contain our geojson data, using geojson format
    gjTracks = {'type':'FeatureCollection', 'features':[]}
    for gpxFile in gpxFiles:
        gpx_df, gpx_points, gpx = gmf.gpxParse(open(os.path.join(inputDir, gpxFile)))
        # add data to heatMapData
        heatMapData = heatMapData.append(gpx_df)
        #
        # add gpx track to map
        trackStart = gpx.time.astimezone(tz.tzlocal()).strftime('%Y-%m-%d  %H:%M')
        geojsonProperties = {
                'Time'     : trackStart,
                'Distance' : '{0:.2f} km'.format(gpx.length_3d()/1000),
                'Duration' : '{0:s}'     .format(str(timedelta(seconds=gpx.get_duration()))),
                'Climbed'  : '{0:d} m'   .format(int(gpx.get_uphill_downhill().uphill)),
                'Descended': '{0:d} m'   .format(int(gpx.get_uphill_downhill().downhill)),
                }
        feature = gmf.df_to_geojsonF(gpx_df, properties=geojsonProperties),
        # some bug
        if type(feature) is tuple:
            feature = feature[0]
        # add this feature (aka, converted dataframe) to the list of features inside our dict
        gjTracks['features'].append(feature)

    fplugins.HeatMap(
            data=heatMapData[['Latitude', 'Longitude']],
            name='Heat map',
            radius=12,
            #max_zoom=13,
            show=False,
            ).add_to(fmap)

    folium.GeoJson(
            gjTracks,
            tooltip=folium.GeoJsonTooltip(fields=['Time'], labels=False),
            popup=folium.GeoJsonPopup(fields=list(geojsonProperties.keys())),
            style_function     = lambda x: {'color':'blue', 'weight':3, 'opacity':.5},
            highlight_function = lambda x: {'color':'red',  'weight':3, 'opacity':1},
            name='GPX tracks'
            ).add_to(fmap)

    fmap.add_child(folium.LayerControl())

    # save map
    outputDir = mapDir
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    fmap.save(os.path.join(mapDir, 'map_{0:s}.html'.format(activityType)))

logging.info('Done')
logging.info('')
