
import numpy as np
from PIL import Image

import sys
np.set_printoptions(threshold=sys.maxsize)

import libs.parkrun_api.parkrun_api as parkrun
import libs.coordinates as coords

# countries = parkrun.Country.GetAllCountries()
# print([country.url for country in countries])

events = parkrun.Event.GetAllEvents()
# print([(event.latitude, event.longitude) for event in events])

MAP_WIDTH = 2000
MAP_HEIGHT = 1000

img_buffer = np.ones((MAP_HEIGHT, MAP_WIDTH), dtype=np.uint8) * 255

def process_event(event: parkrun.Event, img: np.ndarray):
    merc_x, merc_y = coords.latlon_to_mercator(event.latitude, event.longitude, MAP_WIDTH, MAP_HEIGHT)
    merc_x = int(round(merc_x))
    merc_y = int(round(merc_y))
    img[merc_y, merc_x] = 0

for event in events:
    process_event(event, img_buffer)

# print(img_buffer)

img = Image.fromarray(img_buffer)
img.save("result.png")
