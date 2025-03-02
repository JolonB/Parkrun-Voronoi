import numpy as np
from pyproj import CRS, Transformer

latlon = CRS.from_string("EPSG:4326")

mercator = CRS.from_string("EPSG:3857")
# mercator = CRS.from_string("ESRI:53004")  # possibly better

ecef = CRS.from_string("EPSG:4978")
# ecef = CRS.from_string("EPSG:6500")

EARTH_RADIUS = 1.0 * mercator.ellipsoid.semi_major_metre  # 6378137.0 metres
EARTH_CIRCUMFERENCE = 2 * np.pi * EARTH_RADIUS

tf_latlon_to_mercator = Transformer.from_crs(latlon, mercator)
tf_latlon_to_ecef = Transformer.from_crs(latlon, ecef)
tf_ecef_to_latlon = Transformer.from_crs(ecef, latlon)
tf_ecef_to_mercator = Transformer.from_crs(ecef, mercator)

def latlon_to_ecef(latitude, longitude):
    points = tf_latlon_to_ecef.transform(latitude, longitude, 0)
    return (points[0]/EARTH_RADIUS, points[1]/EARTH_RADIUS, points[2]/EARTH_RADIUS)

def ecef_to_latlon(x, y, z):
    x = x * EARTH_RADIUS
    y = y * EARTH_RADIUS
    z = z * EARTH_RADIUS
    return tf_ecef_to_latlon.transform(x, y, z)[:2]

def latlon_to_mercator(latitude, longitude):
    return tf_latlon_to_mercator.transform(latitude, longitude)

def ecef_to_mercator(x, y, z):
    return tf_ecef_to_mercator.transform(x, y, z)[:2]

def mercator_to_array(merc_x, merc_y, map_width, map_height):
    merc_x = (merc_x / EARTH_CIRCUMFERENCE + 0.5) * map_width
    merc_y = (0.5 - merc_y / EARTH_CIRCUMFERENCE) * map_height
    return int(round(merc_x)), int(round(merc_y))

def pixels_between_mercator_points(merc_x1, merc_y1, merc_x2, merc_y2, map_width, map_height):
    """
    The number of pixels between two points on a mercator map, following the great circle path

    Just return max(map_width,map_height) / 2 for now, as I don't know how to actually calculate this.
    There should never be two points more than this distance apart (I think).
    """
    return int(round(max(map_width, map_height) / 2))
