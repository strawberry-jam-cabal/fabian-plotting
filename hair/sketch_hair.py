import math
from random import random
import vsketch
from vsketch import Param, Vsketch
import shapely.geometry as g
import shapely.affinity as a


def regular_polygon(sides: int) -> g.Polygon:
    angle = 2*math.pi / sides
    r = complex(math.cos(angle), math.sin(angle))
    points = [(0+1j) * r**i for i in range(sides)]
    return g.Polygon((c.real, c.imag) for c in points)


def grid(vsk: Vsketch, cols: int, rows: int, scale: float):
    return vsk.noise([x*scale for x in range(cols)], [y*scale for y in range(rows)])


def hair(vsk, x, y, frequency, step_size, fuel=10) -> g.LineString:
    result = [(x, y)]
    while fuel > 0:
        fuel -=1
        angle = vsk.noise(x*frequency, y*frequency) * 2 * math.pi
        x += math.cos(angle)*step_size
        y += math.sin(angle)*step_size
        result.append((x, y))
    return g.LineString(result)


class HairSketch(vsketch.SketchClass):
    size = Param(14.0)
    frequency = Param(0.1)
    steps = Param(20)
    fuel = Param(20)
    detail = Param(0.25)

    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.penWidth(".1mm")

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
        starts = [complex(random()*(self.steps+6) - 3, random()*(self.steps+6) - 3) for _ in range((self.steps+6)**2)]
        for c in starts:
            x = c.real
            y = c.imag
            strand = hair(vsk, x, y, self.frequency, self.detail, fuel=self.fuel).intersection(bounds)
            if strand.geom_type in ["LineString", "MultiLineString"]:
                vsk.geometry(strand)

        layout = f"layout 4.5inx6.25in"
        pen = "penwidth .3mm color black color -l2 green"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    HairSketch.display()
