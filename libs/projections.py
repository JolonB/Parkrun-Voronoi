from pyproj import CRS, Transformer

EQUATOR

latlon = CRS.from_string("EPSG:4326")

mercator = CRS.from_string("EPSG:3857")
# mercator = CRS.from_string("ESRI:53004")  # possibly better

ecef = CRS.from_string("EPSG:4978")
# ecef = CRS.from_string("EPSG:6500")

tf_latlon_to_mercator = Transformer.from_crs(latlon, mercator)
tf_latlon_to_ecef = Transformer.from_crs(latlon, ecef)
tf_ecef_to_latlon = Transformer.from_crs(ecef, latlon)
tf_ecef_to_mercator = Transformer.from_crs(ecef, mercator)

def latlon_to_ecef(latitude, longitude):
    return tf_latlon_to_ecef.transform(latitude, longitude, 0)

def ecef_to_latlon(x, y, z):
    return tf_latlon_to_ecef.transform(x, y, z)[:2]

def latlon_to_mercator(latitude, longitude):
    return tf_latlon_to_mercator.transform(latitude, longitude)

def ecef_to_mercator(x, y, z):
    return tf_ecef_to_mercator.transform(x, y, z)[:2]
