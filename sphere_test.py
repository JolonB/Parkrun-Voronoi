import os
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.spatial import SphericalVoronoi, geometric_slerp

import libs.parkrun_api.parkrun_api as parkrun
import libs.coordinates as coords

events: List[parkrun.Event] = parkrun.Event.GetAllEvents()

points = [coords.latlon_to_ecef(event.latitude, event.longitude) for event in events][:257]  # TODO fails at 258
points_norm = np.array([point / np.linalg.norm(point) for point in points])  # TODO probably doesn't need to be normalised
# print(points_norm)

radius = 1
center = np.array([0, 0, 0])
sv = SphericalVoronoi(points_norm, radius, center)
sv.sort_vertices_of_regions()
t_vals = np.linspace(0, 1, 2000)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
u = np.linspace(0, 2 * np.pi, 100)
v = np.linspace(0, np.pi, 100)
x = np.outer(np.cos(u), np.sin(v))
y = np.outer(np.sin(u), np.sin(v))
z = np.outer(np.ones(np.size(u)), np.cos(v))
ax.plot_surface(x, y, z, color='y', alpha=0.1)
ax.scatter(points_norm[:, 0], points_norm[:, 1], points_norm[:, 2], c='b')
ax.scatter(sv.vertices[:, 0], sv.vertices[:, 1], sv.vertices[:, 2],
                   c='g', alpha=0.2)
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
# breakpoint()
# try:
#     os.mkdir('output')
# except FileExistsError:
#     pass

# for i in range(36):
#     ax.azim = 10*i
#     ax.elev = 10
#     # fig.set_size_inches(4, 4)
#     plt.savefig('output/foo_{}.png'.format(i))

########################################
# FLATTEN IMAGE
########################################

class Shape:
    PLUS = 0
    CROSS = 1
    POINT = 3

def add_latlon_to_map(latitude: float, longitude: float, img: np.ndarray, shape: Shape):
    merc_x, merc_y = coords.latlon_to_mercator(latitude, longitude, MAP_WIDTH, MAP_HEIGHT)
    # if merc_y < 0:
    #     return
    merc_x = int(round(merc_x))
    merc_y = int(round(merc_y))
    img[merc_y, merc_x] = 0
    if shape == Shape.PLUS:
        img[merc_y-1, merc_x] = 0
        img[merc_y+1, merc_x] = 0
        img[merc_y, merc_x-1] = 0
        img[merc_y, merc_x+1] = 0
    elif shape == Shape.CROSS:
        img[merc_y-1, merc_x-1] = 0
        img[merc_y-1, merc_x+1] = 0
        img[merc_y+1, merc_x-1] = 0
        img[merc_y+1, merc_x+1] = 0
    elif shape == Shape.POINT:
        pass  # no more needs to be drawn


vertices_latlon = np.zeros((len(sv.vertices), 2))
for index, vertex in enumerate(sv.vertices):
    vertices_latlon[index] = coords.ecef_to_latlon(*vertex)
    if round(vertices_latlon[index][0],2) == 88.58:
        breakpoint()
    elif round(vertices_latlon[index][1], 2) == 42.40:
        breakpoint()

MAP_WIDTH = 2000
MAP_HEIGHT = 1000
img_buffer = np.ones((MAP_HEIGHT+1, MAP_WIDTH+1), dtype=np.uint8) * 255

# for region in sv.regions[:500]:
#     n = len(region)
#     for i in range(n):
#         start = sv.vertices[region][i]
#         end = sv.vertices[region][(i + 1) % n]
#         try:
#             edge_ecef = geometric_slerp(start, end, t_vals)
#         except ValueError as e:
#             print(e)
#             print((start, end))
#         edge_latlon = []
#         for point_ecef in edge_ecef:
#             point_latlon = coords.ecef_to_latlon(*point_ecef)
#             try:
#                 if np.all(np.round(edge_latlon[-1], 2) == np.round(point_latlon, 2)):
#                     continue
#             except IndexError as e:
#                 pass
#             edge_latlon.append(point_latlon)
#         # edge_latlon = [coords.ecef_to_latlon(*point) for point in edge_ecef]
#         for point in edge_latlon:
#             try:
#                 add_latlon_to_map(point[0], point[1], img_buffer, Shape.POINT)
#             except Exception as e:
#                 print(e)
#                 print((start, end))
#                 print((edge_latlon[0], edge_latlon[-1]))
#                 print(point)


for vertex in vertices_latlon:
    add_latlon_to_map(vertex[0], vertex[1], img_buffer, Shape.PLUS)

for event in events:
    add_latlon_to_map(event.latitude, event.longitude, img_buffer, Shape.CROSS)

img = Image.fromarray(img_buffer)
img.save("map.png")

# breakpoint()