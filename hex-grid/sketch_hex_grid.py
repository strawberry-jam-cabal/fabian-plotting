import cmath
import itertools
import math
import random

import shapely.affinity as a
import shapely.geometry as g
import vsketch
from vsketch import Param, Vsketch


# good seeds:
# 1174536076


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


def rotation(angle: float) -> complex:
    """A rotation of the unit vector by the given angle in radians."""
    return complex(math.cos(angle), math.sin(angle))


class HexGridSketch(vsketch.SketchClass):
    page_size = Param("6inx9in", choices=["8.5inx11in", "6inx9in", "4.5inx6.25in"])
    scale = Param(1.5)
    offset = Param(1.0)
    pen_width = Param(0.2)

    fuel = Param(6)
    forward_prob = Param(0.95)
    branch_prob = Param(0.4)
    layer_prob = Param(0.5)
    fill_chance = Param(0.15)
    gap = Param(0.04)
    min_scale = Param(1/16)

    def inset(self, v: complex) -> complex:
        v_index = round(cmath.phase(v*(0-1j)) / (math.pi*2) * 6)
        up = complex(-1/4, 1/math.sqrt(3)/4)
        inset = [up, up.conjugate()]
        return inset[v_index % 2]

    def walk(self, vsk: Vsketch) -> None:
        shape = a.rotate(regular_polygon(6, 0+1j), 90)
        branches = [1+0j, rotation(math.pi/3), rotation(-math.pi/3)]
        branch_probs = [self.forward_prob, self.branch_prob, self.branch_prob]
        layer_scale = 0.5
        margin = -0.001

        debug = False

        start_directions = polygon_vertices(complex(0, math.sqrt(3)), 6)
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
                x += v * self.inset(v)
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

        for p in result:
            if random.random() < self.fill_chance:
                vsk.fill(2)
                vsk.geometry(p.buffer(-self.gap))
            else:
                vsk.noFill()
                stroke = max(1, round(self.scale * p.boundary.length / math.sqrt(2)))
                # do manual stroke weight to make sure we are only on the inside of the shape
                offset = self.pen_width/10/2
                for i in range(stroke):
                    vsk.geometry(p.buffer(-self.gap-(i*offset)))

    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.centered = False
        # smaller to make the fill look good
        vsk.penWidth(f"{self.pen_width/2}mm")

        self.walk(vsk)

        layout = f"layout {self.page_size} translate -- 0 -{self.offset}cm"
        pen = f"penwidth {self.pen_width}mm color black color -l3 green"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt")


if __name__ == "__main__":
    HexGridSketch.display()
