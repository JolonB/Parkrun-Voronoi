import os
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.spatial import SphericalVoronoi, geometric_slerp

import libs.parkrun_api.parkrun_api as parkrun
import libs.coordinates as coords
import libs.projections as proj

GENERATE_SPHERE_PLOT = False

print("Getting parkrun events")
events: List[parkrun.Event] = parkrun.Event.GetAllEvents()
adult_events = [event for event in events if event.seriesId == 1]
junior_events = [event for event in events if event.seriesId == 2]


points = [proj.latlon_to_ecef(event.latitude, event.longitude) for event in adult_events]
points_norm = np.array([point / np.linalg.norm(point) for point in points])  # TODO probably doesn't need to be normalised

print("Calculating spherical voronoi")
radius = 1
center = np.array([0, 0, 0])
sv = SphericalVoronoi(points_norm, radius, center)
sv.sort_vertices_of_regions()
t_vals = np.linspace(0, 1, 2000)

if GENERATE_SPHERE_PLOT:
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

class Shape:
    PLUS = 0
    CROSS = 1
    POINT = 3

def add_latlon_to_map(latitude: float, longitude: float, img: np.ndarray, shape: Shape):
    # Skip points if above or below mercator projection
    if latitude < -85 or latitude > 85:
        return
    merc_x, merc_y = proj.latlon_to_mercator(latitude, longitude)
    merc_x, merc_y = proj.mercator_to_array(merc_x, merc_y, MAP_WIDTH, MAP_HEIGHT)
    img[merc_y, merc_x] = 0
    # Draw rest of shape, being aware of the bounds of the image
    if shape == Shape.PLUS:
        try:
            img[merc_y-1, merc_x] = 0
        except IndexError:
            pass
        try:
            img[merc_y+1, merc_x] = 0
        except IndexError:
            pass
        try:
            img[merc_y, merc_x-1] = 0
        except IndexError:
            pass
        try:
            img[merc_y, merc_x+1] = 0
        except IndexError:
            pass
    elif shape == Shape.CROSS:
        try:
            img[merc_y-1, merc_x-1] = 0
        except IndexError:
            pass
        try:
            img[merc_y-1, merc_x+1] = 0
        except IndexError:
            pass
        try:
            img[merc_y+1, merc_x-1] = 0
        except IndexError:
            pass
        try:
            img[merc_y+1, merc_x+1] = 0
        except IndexError:
            pass
    elif shape == Shape.POINT:
        pass  # no more needs to be drawn

print("Converting voronoi vertices to latlon")
vertices_latlon = np.zeros((len(sv.vertices), 2))
for index, vertex in enumerate(sv.vertices):
    vertices_latlon[index] = proj.ecef_to_latlon(*vertex)
    if round(vertices_latlon[index][0],2) == 88.58:
        breakpoint()
    elif round(vertices_latlon[index][1], 2) == 42.40:
        breakpoint()

MAP_WIDTH = 2044
MAP_HEIGHT = 2044
img_buffer = np.ones((MAP_HEIGHT, MAP_WIDTH), dtype=np.uint8) * 255

print("Adding edges to map")
for region in sv.regions[:100]:
    n = len(region)
    for i in range(n):
        start = sv.vertices[region][i]
        end = sv.vertices[region][(i + 1) % n]
        # t_vals = np.linspace(0, 1, proj.pixels_between_mercator_points(*start, *end, MAP_WIDTH, MAP_HEIGHT))
        try:
            edge_ecef = geometric_slerp(start, end, t_vals)
        except ValueError as e:
            print(e)
            print((start, end))
        edge_latlon = []
        for point_ecef in edge_ecef:
            point_latlon = proj.ecef_to_latlon(*point_ecef)
            try:
                if np.all(np.round(edge_latlon[-1], 2) == np.round(point_latlon, 2)):
                    continue
            except IndexError as e:
                pass
            edge_latlon.append(point_latlon)
        # breakpoint()  # TODO why aren't these coordinates being put in the correct location?
        ## TODO perhaps something to do with ecef_to_latlon
        # edge_latlon = [coords.ecef_to_latlon(*point) for point in edge_ecef]
        for point in edge_latlon:
            try:
                add_latlon_to_map(point[0], point[1], img_buffer, Shape.POINT)
                # print("Drawing {}".format(point))
            except Exception as e:
                print(e)
                print((start, end))
                print((edge_latlon[0], edge_latlon[-1]))
                print(point)


for vertex in vertices_latlon:
    add_latlon_to_map(vertex[0], vertex[1], img_buffer, Shape.PLUS)

print("Adding events to map")
for event in adult_events:
    add_latlon_to_map(event.latitude, event.longitude, img_buffer, Shape.CROSS)

background = Image.open("assets/Mercator_projection_Square.jpg")
# Apply the mask
background = background.convert("L")
background = np.array(background)
background[img_buffer == 0] = 0
img = Image.fromarray(background)
img.save("map.png")

# img = Image.fromarray(img_buffer)
# img.save("map.png")

# breakpoint()