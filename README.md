# Parkrun-Voronoi

![map of adult parkrun locations](map.png)

As you may know if you are a parkrunner, the 5K app contains a map that can have a Voronoi layer applied on top of it.
This produces regions, each containing one parkrun, within which each location is closer to the contained parkrun than it is to any other parkrun.
There is only one problem with the one in the 5K app: it doesn't take into account the shape of the earth.
This is clear because all of the points are straight, but they should actually curve, particularly as they get closer to the poles.
This means that the 5K app calculated the Voronoi points using points that had already been projected to the Mercator space.
Their map also doesn't wrap around at the international date line, meaning Voronoi regions are cut off at this point.
But I don't blame the 5K app developers for this, it's a lot of annoying maths to get it working correctly.
In fact, my map probably isn't even perfect, but I guess it's a bit more accurate.

You can also run this with your own dataset.
Refer to [Example CSVs](#Example-CSVs) for more information.

## Running

Set up virtual environment with:

```shell
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

The simplest way to run the program is like so:

```
python generate_parkrun_voronoi.py
```

This could take up to a few minutes to generate, depending on your hardware.

The optional command line arguments are as follows:

```
usage: generate_parkrun_voronoi.py [-h] [--csv CSV] [--junior] [--dpi DPI] [--drawlocs] [--drawverts] [--printstats]

Generate a Voronoi diagram of parkrun events

optional arguments:
  -h, --help    show this help message and exit
  --csv CSV     CSV file to read coordinates from
  --junior      Use junior parkrun events. Ignored if --csv is used
  --dpi DPI     DPI of output image
  --drawlocs    Draw location points
  --drawverts   Draw Voronoi vertices
  --printstats  Print statistics about the Voronoi diagram
```

## Stats

At the time of writing this, using the set of 2147 adult parkruns there are a total of 4290 vertices that form Voronoi regions.

The 20 largest parkrun Voronoi regions are as follows:

| # | Location | Area (km^2) |
| --- | --- | --- |
| 1 | Cape Pembroke Lighthouse | 61737724.9 |
| 2 | Presint 18 | 24001967.6 |
| 3 | Gisborne | 21377014.0 |
| 4 | Chuo koen | 20118320.1 |
| 5 | Swakopmund | 14173738.4 |
| 6 | Byxbee | 13880682.3 |
| 7 | Weedon Island Preserve | 13494571.7 |
| 8 | Pokkinen | 12548898.7 |
| 9 | Whangarei | 11637846.0 |
| 10 | Birchwood Trails | 10358936.9 |
| 11 | Louis Trichardt | 10253438.6 |
| 12 | Yuuka Family Road | 9562049.4 |
| 13 | Ryan Bonaminio | 9554677.6 |
| 14 | Himmel | 9302677.2 |
| 15 | Margaret River | 8826735.4 |
| 16 | Etna | 8540430.8 |
| 17 | Terry Hershey | 8500895.3 |
| 18 | Corner Brook Stream Trail | 8372662.3 |
| 19 | Salento | 7994626.3 |
| 20 | Uditore | 7761246.7 |

And the (much less impressive) 10 smallest Voronoi regions are:

| # | Location | Area (km^2) |
| --- | --- | --- |
| 1 | Burswood Peninsula | 5.2 |
| 2 | Dulwich | 7.1 |
| 3 | Peckham Rye | 8.3 |
| 4 | Catford | 8.5 |
| 5 | Alexandra | 10.4 |
| 6 | Hilly Fields | 10.5 |
| 7 | Brockwell | 10.5 |
| 8 | Falls | 10.7 |
| 9 | Clapham Common | 11.2 |
| 10 | Fletcher Moss | 11.3 |

## Example CSVs

Refer to the example CSV files in the csv directory, `capital_cities_starting_with_W.csv`, `settings_of_animated_movies.csv`, and `some_points.csv` for help setting up a custom CSV file of your own.
Run the following command to generate an image using custom data:

```shell
python generate_parkrun_voronoi.py --csv csv/settings_of_animated_movies.csv
```

A CSV file should contain either 2 or 3 columns.
The first two columns must always be latitude and longitude, respectively, in degrees.
The optional third column should be a name for the point, which is useful if using the `--printstats` flag.
If only some locations have a name, you should make sure all rows have 3 columns and not just the ones with names.
The third column can be produced by appending a single comma to the end of a 2 column line.

## My Approach

As much as I enjoy maths, I'm not very familiar with map projections, so all of my previous attempts resulted in slow code that produced incorrect results.
That was until I found the SciPy SphereicalVoronoi and the Matplotlib Basemap classes.
These libraries handle everything I needed.
Special thanks to the Parkrun-API-Python library too.

My approach involves 3 main steps:

### Step 1 - Fetch event data

Using the Parkrun-API-Python library, I pull the data representing all parkrun events around the world.
This data includes the latitude and longitude of each event.
The code filters out the children and adult events, as drawing both at once would take even longer, and would require filtering out points at the same location.

### Step 2 - Generate Voronoi points

Voronoi points cannot simply be calculated on a map using a Mercator projection, as is done for the 5K app.
They need to be computed on a sphere, which the SphericalVoronoi class can fortunately handle (unless you have <=3 points, which it can't handle for some reason).
The points must be converted from (latitude,longitude) to (x,y,z) coordinates in a unit sphere.
This is very similar to the [ECEF coordinate system](https://en.wikipedia.org/wiki/Earth-centered,_Earth-fixed_coordinate_system), just normalised so each vector has a length of 1.

After processing, the SphericalVoronoi class contains the coordinates of the Voronoi vertices, which we convert back to (latitude,longitude), and information about which vertices define each region.

### Step 3 - Generate map

Since a Mercator projection is the map most people are most familiar with (besides, maybe, a globe but I didn't want to make something interactive), everything needs to be converted to Mercator coordinates.
The lines between the vertices also need to curve as the follow a great circle arc.
Luckily, the Basemap class can handle this with relative ease.
The only quirk I experienced was that sometimes the great circle arc would be broken, which was fixed by simply redrawing it (although this then needs to handle lines wrapping around the map).

The arcs are also drawn with varying thicknesses, depending on the length of them.
This means that areas with a high number of parkruns will be more visible as the lines will be thinner.
They still aren't fully visible, especially near London.
However, at that sort of scale, great circle arcs can be approximated as straight lines, so the Voronoi regions are practically identical to the ones in the 5K app.
