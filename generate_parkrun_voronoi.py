import argparse
import os
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import SphericalVoronoi, geometric_slerp

import libs.parkrun_api.parkrun_api as parkrun
import libs.projections as proj
import libs.mapping as mapping

parser = argparse.ArgumentParser(
    description="Generate a Voronoi diagram of parkrun events"
)
parser.add_argument("--csv", type=str, help="CSV file to read coordinates from")
parser.add_argument(
    "--junior",
    action="store_true",
    help="Use junior parkrun events. Ignored if --csv is used",
)
parser.add_argument("--dpi", type=int, default=2000, help="DPI of output image")
parser.add_argument("--drawlocs", action="store_true", help="Draw location points")
parser.add_argument("--drawverts", action="store_true", help="Draw Voronoi vertices")
parser.add_argument(
    "--printstats",
    action="store_true",
    help="Print statistics about the Voronoi diagram",
)

args = parser.parse_args()

DRAW_VORONOI_VERTICES = args.drawverts
DRAW_EVENT_POINTS = args.drawlocs
JUNIOR_PARKRUN = args.junior
IMG_DPI = args.dpi
GENERATE_CSV = args.csv is not None

########################################
# Get points
########################################


class Location:
    def __init__(self, latitude, longitude, name=""):
        self.latitude = latitude
        self.longitude = longitude
        self.name = name if name else "Unnamed"

    def __str__(self):
        return "{}: ({}, {})".format(self.name, self.latitude, self.longitude)

    def __repr__(self):
        return "{},{},{}".format(self.latitude, self.longitude, self.name)


print("Preparing location data")
if GENERATE_CSV:
    filename = args.csv
    if not os.path.exists(filename):
        print("Error: CSV file {} not found".format(filename))
        exit(1)
    points_data = np.genfromtxt(filename, dtype=str, delimiter=",").tolist()
    num_columns = len(points_data[0])
    if num_columns == 2:
        locations = [
            Location(float(point[0]), float(point[1])) for point in points_data
        ]
    elif num_columns == 3:
        locations = [
            Location(float(point[0]), float(point[1]), point[2])
            for point in points_data
        ]
    else:
        print(
            "Error: CSV file must have two or three columns (latitude, longitude, optional name). Has {}".format(
                num_columns
            )
        )
        exit(1)
else:
    events: List[parkrun.Event] = parkrun.Event.GetAllEvents()
    adult_events = [event for event in events if event.seriesId == 1]
    junior_events = [event for event in events if event.seriesId == 2]
    events = junior_events if JUNIOR_PARKRUN else adult_events
    locations = [
        Location(event.latitude, event.longitude, event.shortName) for event in events
    ]

points = [
    proj.latlon_to_ecef(location.latitude, location.longitude) for location in locations
]
points_norm = np.array([point / np.linalg.norm(point) for point in points])

########################################
# Calculate Voronoi
########################################

print("Calculating spherical voronoi")
radius = 1
center = np.array([0, 0, 0])
sv = SphericalVoronoi(points_norm, radius, center)
sv.sort_vertices_of_regions()
t_vals = np.linspace(0, 1, 2000)

########################################
# Mercator Plot
########################################

flat_map = mapping.Map(mapping.MapType.MERCATOR, quality="l")

print("Converting voronoi vertices to latlon")
vertices_latlon = np.zeros((len(sv.vertices), 2))
for index, vertex in enumerate(sv.vertices):
    vertices_latlon[index] = proj.ecef_to_latlon(*vertex)

print("Drawing great circles")
for region in sv.regions:
    n = len(region)
    for i in range(n):
        start = vertices_latlon[region][i]
        end = vertices_latlon[region][(i + 1) % n]
        try:
            flat_map.drawgreatcircle_simple(
                start,
                end,
                method=mapping.GreatCircleMethod.REDRAW,
                linewidth=0.05,
                zorder=10,
            )
        except Exception as e:
            pass

if DRAW_EVENT_POINTS:
    print("Drawing location points")
    flat_map.scatter(
        [location.longitude for location in locations],
        [location.latitude for location in locations],
        latlon=True,
        c="r",
        marker="x",
        s=0.1,
        linewidth=0.05,
        zorder=2,
    )
if DRAW_VORONOI_VERTICES:
    print("Drawing Voronoi vertices")
    flat_map.scatter(
        vertices_latlon[:, 1],
        vertices_latlon[:, 0],
        latlon=True,
        c="b",
        marker="x",
        s=1,
    )

if flat_map.map_type == mapping.MapType.MERCATOR:
    plt.tight_layout(pad=0)
    plt.savefig("map.png", bbox_inches="tight", pad_inches=0.0, dpi=IMG_DPI)
elif flat_map.map_type == mapping.MapType.ROBINSON:
    plt.savefig("map.png", dpi=IMG_DPI)

# TODO see mapping.py
# TODO tidy up code
# TODO calculate area of regions
