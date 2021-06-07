#!/usr/bin/env python3

import configparser
from datetime import date, datetime
import os, socket
import logging
from garminconnect import Garmin
import gmFunctions as gmf

#===============================================================================
# Data and config
#
config = configparser.ConfigParser()
config.read(os.path.join(os.path.expanduser('~'), '.python-github.cfg'))
GARMIN_ID = config.get('garmin.maps', 'GARMIN_ID')
GARMIN_PW = config.get('garmin.maps', 'GARMIN_PW')
GARMIN_AC = config.get('garmin.maps', 'GARMIN_ACTIVITIES')
GARMIN_DS = config.get('garmin.maps', 'GARMIN_DATESTART')

activityTypes = GARMIN_AC.strip().replace(' ', '').split(',')
cpDateStart     = [int(ymd) for ymd in GARMIN_DS.strip().split('-')]

today     = date.today()
dateStart = date(cpDateStart[0], cpDateStart[1], cpDateStart[2])
dateEnd   = today

gpxDir = 'gpxFiles'
mapDir = 'maps'

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
# Init Garmin client and log in
#
client = Garmin(GARMIN_ID, GARMIN_PW)
client.login()
fullName   = client.get_full_name()
unitSystem = client.get_unit_system()
todayStats = client.get_stats(today.isoformat()) # TODO unused for now

logging.info('Garmin user: ' + fullName)
logging.info('Unit system: ' + unitSystem)

#===============================================================================
# Save activities to gpx files
#
doneAct = gmf.activitiesToGpx(cpDateStart, dateEnd, client, activityTypes, gpxDir, logging)

#===============================================================================
# Build maps
#
doneMap = gmf.buildMaps(activityTypes, gpxDir, mapDir, logging)
