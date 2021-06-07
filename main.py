#!/usr/bin/env python3

import configparser
from datetime import date, datetime
import os, socket, sys
import logging
import gmFunctions as gmf
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

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

execLog = 'log_exec.log'
msgLog  = 'log_msg.log'
gpxDir = 'gpxFiles'
mapDir = 'maps'

#===============================================================================
# Check whether the script already ran today
#
if os.path.isfile(execLog):

    with open(execLog, 'r') as filehandle:
        lastRun = datetime.fromisoformat( filehandle.readline() )
    
        if lastRun.date() == today:
            # exit
            print('Already run today')
            sys.exit()

#===============================================================================
# Initialize logger
#
logging.basicConfig(filename = msgLog,
                    level = logging.INFO,
                    format = '%(message)s',
                    filemode = 'w')

logging.info('============= start mapping =============')
logging.info('Host: ' + socket.gethostname())
logging.info('Date: ' + datetime.now().strftime('%Y-%m-%d %H:%M'))

#===============================================================================
# Init Garmin client and log in
#
try:
    client = Garmin(GARMIN_ID, GARMIN_PW)
    client.login()
except (
    GarminConnectConnectionError,
    GarminConnectAuthenticationError,
    GarminConnectTooManyRequestsError,
) as err:
    logging.info('Error occurred during Garmin Connect Client login: %s' % err)
    sys.exit()
except Exception:  # pylint: disable=broad-except
    logging.info('Unknown error occurred during Garmin Connect Client login')
    sys.exit()
fullName   = client.get_full_name()
unitSystem = client.get_unit_system()

logging.info('Garmin user: ' + fullName)
logging.info('Unit system: ' + unitSystem)

#===============================================================================
# Save activities to gpx files
#
doneAct = gmf.activitiesToGpx(dateStart, dateEnd, client, activityTypes, gpxDir, logging)

#===============================================================================
# Build maps
#
doneMap = gmf.buildMaps(activityTypes, gpxDir, mapDir, logging)

#===============================================================================
# Update last exec file
#
if (doneAct == 0) and (doneMap == 0):
    # the script ran succesfully
    with open(execLog, 'w') as filehandle:
        filehandle.write(datetime.now().isoformat())
