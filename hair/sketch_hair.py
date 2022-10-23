import math
from random import random
from typing import Tuple
import vsketch
from vsketch import Param, Vsketch
import shapely.geometry as g
import shapely.affinity as a
import numpy as np


def regular_polygon(sides: int) -> g.Polygon:
    angle = 2*math.pi / sides
    r = complex(math.cos(angle), math.sin(angle))
    points = [(0+1j) * r**i for i in range(sides)]
    return g.Polygon((c.real, c.imag) for c in points)


def grid(vsk: Vsketch, cols: int, rows: int, scale: float):
    return vsk.noise([x*scale for x in range(cols)], [y*scale for y in range(rows)])


def hairs(vsk: Vsketch, x_starts: list[float], y_starts: list[float], frequency: float, step_size: float, fuel: int) -> list[g.LineString]:
    xs = np.array(x_starts)
    ys = np.array(y_starts)
    points = [(xs, ys)]
    while fuel > 0:
        fuel -= 1
        (xs, ys) = steps(vsk, xs, ys, frequency, step_size)
        points.append((xs, ys))
    lines = []
    for i in range(len(xs)):
        coords = [(xs[i], ys[i]) for xs, ys in points]
        if coords:
            lines.append(g.LineString(coords))
    return lines


def steps(vsk: Vsketch, xs: np.ndarray, ys: np.ndarray, frequency: float, step_size: float) -> Tuple[np.ndarray, np.ndarray]:
    angles = vsk.noise(xs*frequency, ys*frequency, grid_mode=False) * 2 * math.pi
    new_xs = xs + np.cos(angles)*step_size
    new_ys = ys + np.sin(angles)*step_size
    return (new_xs, new_ys)



class HairSketch(vsketch.SketchClass):
    size = Param(14.0)
    frequency = Param(0.1)
    steps = Param(20)
    fuel = Param(20)
    detail = Param(0.25)
    pen_width = Param(0.3)

    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.penWidth(f"{self.pen_width/3}mm")

        pixel_size = self.size / self.steps

        # implement your sketch here
        # data = grid(vsk, self.steps, self.steps, self.frequency)
        # for x in range(self.steps):
        #     for y in range(self.steps):
        #         with vsk.pushMatrix():
        #             vsk.translate(x*pixel_size - self.size/2, y*pixel_size - self.size/2)
        #             vsk.rotate(data[x][y] * 2 * math.pi)
        #             vsk.line(0, 0, pixel_size, 0)

        vsk.scale(pixel_size)
        vsk.translate(-self.steps/2, -self.steps/2)
        # bounds = g.box(0, 0, self.steps, self.steps)
        bounds = regular_polygon(6).difference(regular_polygon(3).buffer(-.05).difference(g.Point(0,0).buffer(.35)))
        bounds = a.translate(a.scale(bounds, self.steps/2, self.steps/2), self.steps/2, self.steps/2)
        # bounds = bounds.difference(g.Point(self.steps/2, self.steps/2).buffer(self.steps/3))
        # vsk.geometry(bounds)
        vsk.stroke(2)
        starts = [(random()*(self.steps+6) - 3, random()*(self.steps+6) - 3) for _ in range((self.steps+6)**2)]
        strands = hairs(vsk, [x for x, _ in starts], [y for _, y in starts], self.frequency, self.detail, self.fuel)
        for strand in strands:
            clipped = strand.intersection(bounds)
            if clipped.geom_type in ["LineString", "MultiLineString"]:
                vsk.geometry(clipped)

        layout = f"layout 4.5inx6.25in"
        pen = f"penwidth {self.pen_width}mm color black color -l2 green"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    HairSketch.display()
