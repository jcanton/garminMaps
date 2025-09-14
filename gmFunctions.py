# ===============================================================================
# Parse gpx file
#
def gpxParse(fileHandle):
    import gpxpy
    import pandas as pd

    gpx = gpxpy.parse(fileHandle)

    # make DataFrame
    track = gpx.tracks[0]
    segment = track.segments[0]
    # Load the data into a Pandas dataframe (by way of a list)
    data = []
    # segment_length = segment.length_3d()
    gpx_df = pd.DataFrame([])
    for point_idx, point in enumerate(segment.points):
        data.append(
            [
                point.longitude,
                point.latitude,
                point.elevation,
                point.time,
                segment.get_speed(point_idx),
            ]
        )
        columns = ["Longitude", "Latitude", "Altitude", "Time", "Speed"]
        gpx_df = pd.DataFrame(data, columns=columns)

    # make points tuple for line
    gpx_points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                gpx_points.append(tuple([point.latitude, point.longitude]))
    return gpx_df, gpx_points, gpx


# ===============================================================================
# Pandas dataframe to GeoJson feature
# adapted from https://notebook.community/gnestor/jupyter-renderers/notebooks/nteract/pandas-to-geojson
#
def df_to_geojsonF(df, properties={}, lat="Latitude", lon="Longitude"):
    # create a feature template to fill in
    feature = {
        "type": "Feature",
        "properties": properties,
        "geometry": {"type": "LineString", "coordinates": []},
    }

    # loop through each row in the dataframe and add its coordinates
    for _, row in df.iterrows():
        # fill in the coordinates
        feature["geometry"]["coordinates"].append([row[lon], row[lat]])

    return feature


# ===============================================================================
# Save activities to gpx files
#
def activitiesToGpx(dateStart, dateEnd, client, activityTypes, gpxDir, logging):
    import os
    import sys
    from datetime import datetime

    from garminconnect import (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    )

    dateFmt = "%Y-%m-%d"

    logging.info("Selected activities: " + ", ".join(activityTypes))
    logging.info("")
    for activityType in activityTypes:
        logging.info("\tDownloading activities: " + activityType)

        outputDir = os.path.join(gpxDir, activityType)
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)

        try:
            activities = client.get_activities_by_date(
                dateStart.strftime(dateFmt), dateEnd.strftime(dateFmt), activityType
            )
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            logging.info(
                "\tError occurred during Garmin Connect Client get activities: %s" % err
            )
            #sys.exit()
        except Exception as err:  # pylint: disable=broad-except
            logging.info(
                "\tUnknown error occurred during Garmin Connect Client get activities:\n%s"
                % err
            )
            #sys.exit()

        for activity in activities:
            activity_id = activity["activityId"]
            activity_start = datetime.strptime(
                activity["startTimeLocal"], "%Y-%m-%d %H:%M:%S"
            )

            output_file = os.path.join(
                outputDir, "{0:s}.gpx".format(activity_start.strftime("%Y%m%d_%H%M%S"))
            )

            if not os.path.isfile(output_file):
                try:
                    gpx_data = client.download_activity(
                        activity_id, dl_fmt=client.ActivityDownloadFormat.GPX
                    )
                    with open(output_file, "wb") as fb:
                        fb.write(gpx_data)
                except Exception as err:  # pylint: disable=broad-except
                    logging.info(
                        "\tError occurred during Garmin Connect Client download activity:\n%s"
                        % err
                    )

    logging.info("\tDone")
    logging.info("")
    return 0


# ===============================================================================
# Build maps
#
def buildMaps(activityTypes, gpxDir, mapDir, logging):
    import os
    from datetime import timedelta

    import folium
    import pandas as pd
    from dateutil import tz
    from folium import plugins as fplugins

    for activityType in activityTypes:
        logging.info("\tBuilding map for: " + activityType)

        # generate map
        fmap = folium.Map(
            #tiles=None,
            tiles="OpenStreetMap",
            location=[47.34967, 8.53660],
            zoom_start=13,
            control_scale=True,
            prefer_canvas=True,
        )
        #folium.TileLayer("Stamen Terrain", name="Stamen Terrain").add_to(fmap)
        #folium.TileLayer("Stamen Toner", name="Stamen Toner").add_to(fmap)
        #folium.TileLayer("CartoDB dark_matter", name="CartoDB dark matter").add_to(fmap)
        #folium.TileLayer("OpenStreetMap", name="OpenStreet Map").add_to(fmap)
        fplugins.Fullscreen(
            position="topright",
            title="Fullscreen",
            title_cancel="Exit Fullscreen",
            force_separate_button=True,
        ).add_to(fmap)
        #heatMapData = pd.DataFrame([])

        # load gpx files and add tracks to map
        inputDir = os.path.join(gpxDir, activityType)
        gpxFiles = os.listdir(inputDir)
        # create a new python dict to contain our geojson data, using geojson format
        gjTracks = {"type": "FeatureCollection", "features": []}
        for gpxFile in gpxFiles:
            gpx_df, gpx_points, gpx = gpxParse(open(os.path.join(inputDir, gpxFile)))
            ## add data to heatMapData
            #heatMapData = heatMapData.append(gpx_df)
            #
            # add gpx track to map
            trackStart = gpx.time.astimezone(tz.tzlocal()).strftime("%Y-%m-%d  %H:%M")
            geojsonProperties = {
                "Time": trackStart,
                "Distance": "{0:.2f} km".format(gpx.length_3d() / 1000),
                "Duration": "{0:s}".format(str(timedelta(seconds=gpx.get_duration()))),
                "Climbed": "{0:d} m".format(int(gpx.get_uphill_downhill().uphill)),
                "Descended": "{0:d} m".format(int(gpx.get_uphill_downhill().downhill)),
            }
            feature = (df_to_geojsonF(gpx_df, properties=geojsonProperties),)
            # some bug
            if type(feature) is tuple:
                feature = feature[0]
            # add this feature (aka, converted dataframe) to the list of features inside our dict
            gjTracks["features"].append(feature)

        #fplugins.HeatMap(
        #    data=heatMapData[["Latitude", "Longitude"]],
        #    name="Heat map",
        #    radius=12,
        #    # max_zoom=13,
        #    show=False,
        #).add_to(fmap)

        folium.GeoJson(
            gjTracks,
            tooltip=folium.GeoJsonTooltip(fields=["Time"], labels=False),
            popup=folium.GeoJsonPopup(fields=list(geojsonProperties.keys())),
            style_function=lambda x: {"color": "blue", "weight": 3, "opacity": 0.5},
            highlight_function=lambda x: {"color": "red", "weight": 3, "opacity": 1},
            name="GPX tracks",
        ).add_to(fmap)

        fmap.add_child(folium.LayerControl())

        # save map
        outputDir = mapDir
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)

        fmap.save(os.path.join(mapDir, "map_{0:s}.html".format(activityType)))

    logging.info("\tDone")
    logging.info("")
    return 0
