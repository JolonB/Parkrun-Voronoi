import math

def latlon_to_ecef(latitude, longitude):
    """
    Convert latitude and longitude to a 3-dimensional unit vector containing
    coordinates in the Earth-centered, Earth-fixed coordinate system.

    Latitude and longitude are represented as angles.
    0 degrees latitude is at the equator and positive latitude to the north.
    Latitude ranges from -90 to +90 degrees.
    0 degrees longitude is above England (Greenwich meridian) with the anti-
    meridian (180 degrees) being roughly at the international date line.
    Positive longitude goes east from the prime meridian (i.e. over Europe).

    x is the axis going from prime prime meridian to anti-meridian, with the
    prime meridian being positive.
    y is the axis between the east and west hemispheres, with east being
    positive.
    z is the axis going through the poles, with the north pole being positive.
    """
    latitude = math.radians(latitude)
    longitude = math.radians(longitude)

    sin_lat = math.sin(latitude)
    sin_lon = math.sin(longitude)
    cos_lat = math.cos(latitude)
    cos_lon = math.cos(longitude)

    x = cos_lat * cos_lon
    y = cos_lat * sin_lon
    z = sin_lat

    return (x, y, z)

def ecef_to_latlon(x, y, z):
    """
    Convert Earth-centered, Earth-fixed coordinates to latitude and longitude.
    The coordinates are always treated as if they are on the surface of a unit
    sphere, which greatly simplifies the maths.
    """
    latitude = math.asin(z)
    longitude = math.atan2(y, x)

    latitude = math.degrees(latitude)
    longitude = math.degrees(longitude)

    return latitude, longitude

def latlon_to_mercator(latitude, longitude, map_width, map_height):
    x = (longitude + 180) / 360. * map_width
    # Remap the latitude from -90 to +90 -> - to +90 (but in radians)
    lat_0_90 = math.radians(latitude / 2. + 45)
    latitude_distortion = math.log(math.tan(lat_0_90)) / (2 * math.pi)
    y = (map_height / 2.) - (map_width * latitude_distortion)

    return x, y