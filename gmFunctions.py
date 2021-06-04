#===============================================================================
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
    #segment_length = segment.length_3d()
    gpx_df = pd.DataFrame([])
    for point_idx, point in enumerate(segment.points):
        data.append([point.longitude, point.latitude,point.elevation,
        point.time, segment.get_speed(point_idx)])
        columns = ['Longitude', 'Latitude', 'Altitude', 'Time', 'Speed']
        gpx_df = pd.DataFrame(data, columns=columns)

    # make points tuple for line
    gpx_points = []
    for track in gpx.tracks:
        for segment in track.segments: 
            for point in segment.points:
                gpx_points.append(tuple([point.latitude, point.longitude]))
    return gpx_df, gpx_points, gpx

#===============================================================================
# Pandas dataframe to GeoJson feature
# adapted from https://notebook.community/gnestor/jupyter-renderers/notebooks/nteract/pandas-to-geojson
#
def df_to_geojsonF(df, properties={}, lat='Latitude', lon='Longitude'):

    # create a feature template to fill in
    feature = {
            'type':'Feature',
            'properties': properties,
            'geometry':{
                'type':'LineString',
                'coordinates':[]
                }
            }

    # loop through each row in the dataframe and add its coordinates
    for _, row in df.iterrows():
        
        # fill in the coordinates
        feature['geometry']['coordinates'].append( [row[lon],row[lat]] )

    return feature
