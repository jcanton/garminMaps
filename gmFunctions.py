#===============================================================================
# Global modules
#

#===============================================================================
# Parse gpx file
#
def gpxParse(fileName):

    import gpxpy
    import pandas as pd

    gpx = gpxpy.parse(open(fileName))

    # make DataFrame
    track = gpx.tracks[0]
    segment = track.segments[0]
    # Load the data into a Pandas dataframe (by way of a list)
    data = []
    segment_length = segment.length_3d()
    gpx_df = pd.DataFrame([])
    for point_idx, point in enumerate(segment.points):
        data.append([point.longitude, point.latitude,point.elevation,
        point.time, segment.get_speed(point_idx)])
        columns = ['Longitude', 'Latitude', 'Altitude', 'Time', 'Speed']
        gpx_df = pd.DataFrame(data, columns=columns)

    # make points tuple for line
    points = []
    for track in gpx.tracks:
        for segment in track.segments: 
            for point in segment.points:
                points.append(tuple([point.latitude, point.longitude]))
    return gpx_df, points
