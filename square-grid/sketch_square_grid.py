import itertools
import math
import random
from typing import Callable, Tuple

import numpy as np
import pnoise
import shapely.affinity as a
import shapely.geometry as g
import shapely.ops as so
import vsketch
from vsketch import Param, Vsketch


# Good seeds:
# 779799833
# 1815148146


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

    def paths(self, x_starts: list[float], y_starts: list[float], frequency: float, step_size: Callable[[], float], length: int) -> list[g.LineString]:
        assert len(x_starts) == len(y_starts)
        xs = np.array(x_starts)
        ys = np.array(y_starts)
        points = [(xs, ys)]
        while length > 0:
            length -= 1
            (vxs, vys) = self.get_values(xs, ys, frequency)
            step_sizes = np.array([step_size() for _ in range(len(x_starts))])
            vxs = np.multiply(vxs, step_sizes)
            vys = np.multiply(vys, step_sizes)
            xs = xs + vxs
            ys = ys + vys
            points.append((xs, ys))
        lines = []
        for i in range(len(xs)):
            coords = [(xs[i], ys[i]) for xs, ys in points]
            if coords:
                lines.append(g.LineString(coords))
        return lines


def polygon_vertices(start: complex, sides: int) -> list[complex]:
    angle = 2*math.pi / sides
    r = complex(math.cos(angle), math.sin(angle))
    return [start * r**i for i in range(sides)]


def regular_polygon(sides: int, vertex: complex = 0+1j) -> g.Polygon:
    return g.Polygon((c.real, c.imag) for c in polygon_vertices(vertex, sides))


def shuffle(xs):
    res = list(xs)
    random.shuffle(res)
    return res


def remove_overlapping(lines: list[g.LineString], width: float) -> list[g.LineString]:
    if not lines:
        return []

    def hash_point(x: float, y: float) -> Tuple[int, int]:
        return int(x/width), int(y/width)

    all_lines = []
    for line in lines:
        if line.geom_type == "LineString":
            all_lines.append(line)
        elif line.geom_type == "MultiLineString":
            all_lines.extend(line.geoms)
        else:
            print(f"Unknown geometry: {line.geom_type}")

    points = set()
    result = []
    for line in all_lines:
        finished = True
        for i, (x, y) in enumerate(line.coords):
            hashed = hash_point(x, y)
            if hashed in points:
                if i > 1:
                    result.append(g.LineString(line.coords[:i]))
                finished = False
                break
            points.add(hashed)
        if finished:
            result.append(line)

    return result


class SquareGridSketch(vsketch.SketchClass):
    # Sketch parameters:
    page_size = Param("6inx9in", choices=["8.5inx11in", "6inx9in", "4.5inx6.25in"])
    offset = Param(1.0)
    pen_width = Param(0.3)
    scale = Param(1.5)

    fuel = Param(7)
    forward_prob = Param(0.95)
    branch_prob = Param(0.4)
    layer_prob = Param(0.5)
    fill_prob = Param(0.15)
    gap = Param(0.04)
    min_scale = Param(1/16)


    def walk(self, vsk: Vsketch) -> None:
        shape = regular_polygon(4, 0+1j)
        inset = [-0.25+0.25j, -0.25-0.25j]
        branches = [1+0j, 0+1j, 0-1j]
        branch_probs = [self.forward_prob, self.branch_prob, self.branch_prob]
        layer_scale = 0.5
        margin = -0.001

        debug = False

        start_directions = polygon_vertices(1+1j, 4)
        start_positions = [0+0j]

        result = [shape]

        vsk.scale(self.scale)

        todo = list(itertools.product(start_positions, start_directions, [1.0], [self.fuel]))
        while todo:
            x, v, scale, fuel = todo.pop(0)
            prev = x
            x += v

            # should we drop down a layer?
            if random.random() < self.layer_prob:
                scale *= layer_scale
                x += v * random.choice(inset)
                v *= layer_scale

            if scale <= self.min_scale:
                continue

            # are we intersecting things we've already drawn
            this = a.translate(a.scale(shape, scale, scale), x.real, x.imag)
            if any(p.intersects(this.buffer(margin)) for p in result):
                continue

            result.append(this)
            if debug:
                old_stroke = vsk._cur_stroke
                vsk.stroke(3)
                vsk.line(prev.real, prev.imag, x.real, x.imag)
                vsk.circle(x.real, x.imag, .05)
                vsk.line(x.real, x.imag, (x+v).real, (x+v).imag)
                vsk.stroke(old_stroke) if old_stroke is not None else vsk.noStroke()

            if fuel <= 0:
                continue

            # where to go from here
            for branch, prob in shuffle(zip(branches, branch_probs)):
                if random.random() < prob:
                    todo.append((x, v*branch, scale, fuel-1))

        to_fill = []
        for p in result:
            stroke = max(1, round(self.scale * p.boundary.length / math.sqrt(2)))
            # do manual stroke weight to make sure we are only on the inside of the shape
            offset = self.pen_width/10/2
            for i in range(stroke):
                vsk.geometry(p.buffer(-self.gap-(i*offset)))
            if random.random() < self.fill_prob:
                # vsk.fill(2)
                # vsk.geometry(p.buffer(-self.gap))
                # vsk.noFill()
                to_fill.append(p.buffer(-self.gap-(stroke*offset)))

        # Fill Params
        density = 15
        freq = 0.35
        step_size = 1/8
        length = 120
        min_length = 1

        def random_step_size():
            return step_size - random.random() * step_size * 1/2

        fill_union: g.MultiPolygon = so.unary_union(to_fill)
        (min_x, min_y, max_x, max_y) = fill_union.bounds
        num_starts = round((max_x - min_x) * (max_y - min_y) * density)
        xs = [(random.random()*1.2 - .1) * (max_x - min_x) + min_x for _ in range (num_starts)]
        ys = [(random.random()*1.2 - .1) * (max_y - min_y) + min_y for _ in range (num_starts)]
        bg = remove_overlapping(NoiseField().paths(xs, ys, freq, random_step_size, length), self.pen_width/10/4)
        bg = [l for l in bg if l.length > min_length]
        vsk.stroke(2)
        vsk.geometry(fill_union.intersection(so.unary_union(bg)))
        # vsk.stroke(3)
        # vsk.geometry(so.unary_union(bg))


    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.centered = False
        vsk.penWidth(f"{self.pen_width/2}mm")

        self.walk(vsk)

        layout = f"layout {self.page_size} translate -- 0 -{self.offset}cm"
        pen = f"penwidth {self.pen_width}mm color black color -l2 black"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt")


if __name__ == "__main__":
    SquareGridSketch.display()
