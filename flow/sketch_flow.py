from dataclasses import dataclass
import math
import random
from typing import Tuple

import numpy as np
import pnoise
import shapely.affinity as a
import shapely.geometry as g
import shapely.ops as so
import vsketch
from vsketch import Param, Vsketch


def regular_polygon(sides: int) -> g.Polygon:
    angle = 2*math.pi / sides
    r = complex(math.cos(angle), math.sin(angle))
    points = [(0+1j) * r**i for i in range(sides)]
    return g.Polygon((c.real, c.imag) for c in points)


class NoiseField():
    """A 2D noise field generated from two independent Perlin noise samples."""
    def __init__(self) -> None:
        self.x_field = pnoise.Noise()
        self.y_field = pnoise.Noise()

    def get_values(self, xs: np.ndarray, ys: np.ndarray, frequency: float) -> Tuple[np.ndarray, np.ndarray]:
        zeros = np.zeros_like(xs)
        return (
            self.x_field.perlin(xs*frequency, ys*frequency, zeros, grid_mode=False) * 2 - 1,
            self.y_field.perlin(xs*frequency, ys*frequency, zeros, grid_mode=False) * 2 - 1,
        )

    def understep(self, step_size: float, max_understep: float = 1/2) -> float:
        return step_size * (1 - random.random() * max_understep)

    def paths(
        self,
        x_starts: list[float],
        y_starts: list[float],
        frequency: float,
        length: float,
        step_size: float,
        max_understep: float,
        clearance: float,
        min_length: float,
    ) -> list[g.LineString]:
        assert len(x_starts) == len(y_starts)

        hash_point = lambda p: (int(p.real/clearance), int(p.imag/clearance))

        @dataclass
        class Line:
            points: list[complex]
            fuel: float

        lines = [Line([complex(x, y)], length) for x, y in zip(x_starts, y_starts)]
        occupied = {hash_point(line.points[0]): (line, line.fuel) for line in lines}

        while any(line.fuel > 0 for line in lines):
            indices = [i for i in range(len(lines)) if lines[i].fuel > 0]
            xs = np.array([lines[i].points[-1].real for i in indices])
            ys = np.array([lines[i].points[-1].imag for i in indices])
            vxs, vys = self.get_values(xs, ys, frequency)
            vys = vys + ((ys-7) * -.1)
            vxs = vxs + ((xs-7) * -.1)
            step_sizes = np.array([self.understep(step_size, max_understep) for _ in range(len(xs))])
            vxs = np.multiply(vxs, step_sizes)
            vys = np.multiply(vys, step_sizes)
            xs = xs + vxs
            ys = ys + vys

            for i, x, y in zip(indices, xs, ys):
                point = complex(x, y)
                line = lines[i]
                line.fuel -= max(0.1, abs(line.points[-1] - point))
                h = hash_point(point)
                if h in occupied and occupied[h][0] != line:
                    (other, other_fuel) = occupied[h]
                    fuel_diff = line.fuel - other_fuel
                    if fuel_diff > 0:
                        other.fuel += fuel_diff
                        occupied[h] = (other, line.fuel)
                        line.fuel = 0
                        line.points.append(point)
                else:
                    line.points.append(point)
                    occupied[h] = (line, line.fuel)

        result = []
        for line in lines:
            if len(line.points) > 1:
                ls = g.LineString((p.real, p.imag) for p in line.points)
                if ls.length >= min_length:
                    result.append(ls)
        return result


class FlowSketch(vsketch.SketchClass):
    # Sketch parameters:
    page_size = Param("6inx9in", choices=["8.5inx11in", "6inx9in", "4.5inx6.25in", "2.5inx3.75in"])
    offset = Param(1.0)
    pen_width = Param(0.3)
    scale = Param(1.0)

    width = Param(4.0)
    height = Param(10.0)

    density = Param(1.0)
    fuel = Param(60.0)
    min_length = Param(1.0)
    frequency = Param(0.35)
    detail = Param(0.25)
    max_understep = Param(0.5)

    def gen_hairs(self, vsk: Vsketch) -> None:
        crop = g.box(0, 0, self.width, self.height)

        (min_x, min_y, max_x, max_y) = crop.bounds
        num_starts = round((max_x - min_x) * (max_y - min_y) * self.density)
        xs = [(random.random()*1.2 - .1) * (max_x - min_x) + min_x for _ in range (num_starts)]
        ys = [(random.random()*1.2 - .1) * (max_y - min_y) + min_y for _ in range (num_starts)]

        bg = NoiseField().wip_paths(xs, ys, self.frequency, self.fuel, self.detail, self.max_understep, self.pen_width/10, self.min_length)

        circle = lambda r: g.Point(0, 0).buffer(r)
        ring = lambda a, b: circle(a).difference(circle(b))
        shape = a.translate(a.scale(ring(1, 0.95).union(ring(.9, .8)).union(ring(.75, .7)).union(ring(.55, .45)).union(ring(.35, 0)), self.width*.45, self.width*.45), self.width/2, self.height/2)
        # shape = a.translate(a.scale(regular_polygon(6), self.width * 0.6, self.width * 0.6), self.width/2, self.height/2)
        crop = crop.intersection(shape)

        vsk.geometry(crop.intersection(so.unary_union(bg)))

    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.scale(self.scale)
        vsk.centered = False
        vsk.penWidth(f"{self.pen_width/2}mm")

        self.gen_hairs(vsk)

        layout = f"layout {self.page_size} translate -- 0 -{self.offset}cm"
        pen = f"penwidth {self.pen_width}mm color black color -l2 blue"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt linesimplify -t0.01mm")


if __name__ == "__main__":
    FlowSketch.display()
