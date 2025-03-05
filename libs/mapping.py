from enum import Enum

from mpl_toolkits.basemap import Basemap


class MapType(Enum):
    MERCATOR = 0
    ROBINSON = 1


class GreatCircleMethod(Enum):
    DEFAULT = 0
    LOW_RES = 1
    REDRAW = 2


class Map(Basemap):
    def __init__(self, map_type=MapType.MERCATOR, quality="l"):
        if map_type == MapType.MERCATOR:
            super().__init__(
                projection="merc",
                llcrnrlat=-85,
                urcrnrlat=85,
                llcrnrlon=-180,
                urcrnrlon=180,
                lat_ts=20,
                resolution=quality,
            )
        elif map_type == MapType.ROBINSON:
            super().__init__(projection="robin", lon_0=0, resolution=quality)
        else:
            raise ValueError("Invalid map type")
        self.drawcoastlines(linewidth=0.25)
        # self.drawcountries(linewidth=0.25)
        # self.fillcontinents(color='coral')
        # self.drawmapboundary(fill_color='aqua')

    def drawgreatcircle_simple(
        self,
        start,
        end,
        method=GreatCircleMethod.DEFAULT,
        linewidth=1,
        color="b",
        **kwargs
    ):
        # If the angle between the start and end is too small, use a very small del_s
        del_s = 80 if method == GreatCircleMethod.LOW_RES else 100
        if abs(angle_diff(start[0], end[0]) < 5) or abs(
            angle_diff(start[1], end[1]) < 5
        ):
            del_s = 1

        if method == GreatCircleMethod.DEFAULT:
            self.drawgreatcircle(
                start[1],
                start[0],
                end[1],
                end[0],
                del_s=del_s,
                linewidth=linewidth,
                color=color,
                **kwargs
            )
        elif method == GreatCircleMethod.LOW_RES:
            self.drawgreatcircle(
                start[1],
                start[0],
                end[1],
                end[0],
                del_s=del_s,
                linewidth=linewidth,
                color=color,
                **kwargs
            )
        elif method == GreatCircleMethod.REDRAW:
            line, = self.drawgreatcircle(
                start[1],
                start[0],
                end[1],
                end[0],
                del_s=del_s,
                linewidth=linewidth,
                color=color,
                **kwargs
            )
            line.remove()  # TODO technically, I don't think we need to remove it, can maybe just use the getline function
            mx, my = line.get_data()

            # Break the line if it crosses the 180th meridian
            break_index = len(mx)
            for index, (x0, x1) in enumerate(zip(mx, mx[1:])):
                # Detect pairs of points that span close to the entire map
                if abs(x0 - x1) >= (self.xmax - self.xmin) * 0.9:
                    break_index = index + 1

            self.plot(
                mx[:break_index],
                my[:break_index],
                linewidth=linewidth,
                color=color,
                **kwargs
            )
            self.plot(
                mx[break_index:],
                my[break_index:],
                linewidth=linewidth,
                color=color,
                **kwargs
            )


def angle_diff(a, b):
    return (a - b + 180) % 360 - 180
