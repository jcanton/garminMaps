#!/usr/bin/env python3

import configparser
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)
from datetime import date, datetime
import sys, os
quit = sys.exit
#import logging
#logging.basicConfig(level=logging.DEBUG)

config = configparser.ConfigParser()
config.read(os.path.join(os.path.expanduser('~'), '.python-github.cfg'))
GARMIN_ID = config.get('connect.garmin.com', 'GARMIN_ID')
GARMIN_PW = config.get('connect.garmin.com', 'GARMIN_PW')

today     = date.today()
dateStart = date(2019, 1, 1)
dateEnd   = today
dateFmt   = '%Y-%m-%d'


#-------------------------------------------------------------------------------
# Init
#
client = Garmin(GARMIN_ID, GARMIN_PW)
client.login()
fullName = client.get_full_name()
unitSystem = client.get_unit_system()

todayStats = client.get_stats(today.isoformat())

#-------------------------------------------------------------------------------
# Get activities
#
# :param activitytype: (Optional) Type of activity you are searching
#                      Possible values are [cycling, running, swimming,
#                      multi_sport, fitness_equipment, hiking, walking, other]

activityType = 'walking'

outputDir = './activities/{0:s}/'.format(activityType)
if not os.path.exists(outputDir):
    os.makedirs(outputDir)

activities = client.get_activities_by_date(dateStart.strftime(dateFmt), dateEnd.strftime(dateFmt), activityType)

for activity in activities:

    activity_id    = activity['activityId']
    activity_start = datetime.strptime(activity['startTimeLocal'], '%Y-%m-%d %H:%M:%S')

    gpx_data = client.download_activity(activity_id, dl_fmt=client.ActivityDownloadFormat.GPX)

    output_file = outputDir + '{0:s}.gpx'.format(activity_start.strftime('%Y%m%d_%H%M%S'))

    with open(output_file, 'wb') as fb:
        fb.write(gpx_data)
