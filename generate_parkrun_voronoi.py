import os
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import SphericalVoronoi, geometric_slerp

import libs.parkrun_api.parkrun_api as parkrun
import libs.projections as proj
import libs.mapping as mapping

GENERATE_SPHERE_PLOT = False
DRAW_VORONOI_VERTICES = False
DRAW_EVENT_POINTS = True
JUNIOR_PARKRUN = False
SMALL_SAMPLE = False
IMG_DPI = 2000

print("Getting parkrun events")
events: List[parkrun.Event] = parkrun.Event.GetAllEvents()
adult_events = [event for event in events if event.seriesId == 1]
junior_events = [event for event in events if event.seriesId == 2]

event_locations = junior_events if JUNIOR_PARKRUN else adult_events
if SMALL_SAMPLE:
    event_locations = event_locations[:100]

points = [proj.latlon_to_ecef(event.latitude, event.longitude) for event in event_locations]
points_norm = np.array([point / np.linalg.norm(point) for point in points])  # TODO probably doesn't need to be normalised

print("Calculating spherical voronoi")
radius = 1
center = np.array([0, 0, 0])
sv = SphericalVoronoi(points_norm, radius, center)
sv.sort_vertices_of_regions()
t_vals = np.linspace(0, 1, 2000)

if GENERATE_SPHERE_PLOT:  # TODO tidy this up
    print("Generating sphere plot")
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    x = np.outer(np.cos(u), np.sin(v))*.95
    y = np.outer(np.sin(u), np.sin(v))*.95
    z = np.outer(np.ones(np.size(u)), np.cos(v))*.95
    ax.plot_surface(x, y, z, color='y', alpha=0.7)
    ax.scatter(points_norm[:, 0], points_norm[:, 1], points_norm[:, 2], c='b')
    ax.scatter(sv.vertices[:, 0], sv.vertices[:, 1], sv.vertices[:, 2],
                    c='g', alpha=0.05)
    for region in sv.regions:
        n = len(region)
        for i in range(n):
            start = sv.vertices[region][i]
            end = sv.vertices[region][(i + 1) % n]
            result = geometric_slerp(start, end, t_vals)
            ax.plot(result[..., 0],
                    result[..., 1],
                    result[..., 2],
                    c='k')
    try:
        os.mkdir('output')
    except FileExistsError:
        pass

    STEP = 20
    for i in range(360 // STEP):
        print("Drawing {}".format(i))
        ax.azim = STEP*i
        ax.elev = 10
        fig.set_size_inches(4, 4)
        plt.savefig('output/foo_{}.png'.format(i))

########################################
# FLATTEN IMAGE
########################################

flat_map = mapping.Map(mapping.MapType.MERCATOR, quality='l')

print("Converting voronoi vertices to latlon")
vertices_latlon = np.zeros((len(sv.vertices), 2))
for index, vertex in enumerate(sv.vertices):
    vertices_latlon[index] = proj.ecef_to_latlon(*vertex)
    if round(vertices_latlon[index][0],2) == 88.58:
        breakpoint()
    elif round(vertices_latlon[index][1], 2) == 42.40:
        breakpoint()

print("Drawing great circles")
for region in sv.regions:
    n = len(region)
    for i in range(n):
        start = vertices_latlon[region][i]
        end = vertices_latlon[region][(i + 1) % n]
        try:
            flat_map.drawgreatcircle_simple(start, end, method=mapping.GreatCircleMethod.REDRAW, linewidth=0.05, zorder=10)
        except Exception as e:
            pass

if DRAW_EVENT_POINTS:
    print("Drawing events")
    flat_map.scatter([event.longitude for event in event_locations], [event.latitude for event in event_locations], latlon=True, c='r', marker='x', s=0.1, linewidth=0.05, zorder=2)
if DRAW_VORONOI_VERTICES:
    print("Drawing Voronoi vertices")
    flat_map.scatter(vertices_latlon[:, 1], vertices_latlon[:, 0], latlon=True, c='b', marker='x', s=1)

if flat_map.map_type == mapping.MapType.MERCATOR:
    plt.tight_layout(pad=0)
    plt.savefig('map.png', bbox_inches='tight', pad_inches=0.0, dpi=IMG_DPI)
elif flat_map.map_type == mapping.MapType.ROBINSON:
    plt.savefig('map.png', dpi=IMG_DPI)

# TODO remove border around map
# TODO see mapping.py
# TODO increase resolution (dpi)
# TODO tidy up code
# TODO add argparse stuff
# TODO calculate area of regions