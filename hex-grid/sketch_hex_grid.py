import cmath
import itertools
import math
import pathlib
import sys
import random

import shapely.affinity as a
import shapely.geometry as g
import shapely.ops as so
import vsketch
from vsketch import Param, Vsketch

sys.path.append(str(pathlib.Path(__file__).parent.parent))
import util


def rotation(angle: float) -> complex:
    """A rotation of the unit vector by the given angle in radians."""
    return complex(math.cos(angle), math.sin(angle))


class HexGridSketch(vsketch.SketchClass):
    page_size = Param("6inx9in", choices=["11inx15in", "8.5inx11in", "6inx9in", "4.5inx6.25in"])
    scale = Param(1.5)
    offset = Param(1.0)
    pen_width = Param(0.2)

    fuel = Param(6)
    forward_prob = Param(0.95)
    branch_prob = Param(0.4)
    layer_prob = Param(0.5)
    fill_prob = Param(0.15)
    gap = Param(0.04)
    max_levels = Param(4)

    fill = Param("flow", choices=["flow", "solid", "none"])
    bubbles = Param(False)
    multi_stroke = Param(True)


    def inset(self, v: complex) -> complex:
        v_index = round(cmath.phase(v*(0-1j)) / (math.pi*2) * 6)
        up = complex(-1/4, 1/math.sqrt(3)/4)
        inset = [up, up.conjugate()]
        return inset[v_index % 2]


    def flow_fill(self, to_fill) -> None:
        density = 20.0
        freq = 0.35
        step_size = 1/8
        length = 4
        min_length = .1

        fill_union: g.MultiPolygon = so.unary_union(to_fill)
        (min_x, min_y, max_x, max_y) = fill_union.bounds
        num_starts = round((max_x - min_x) * (max_y - min_y) * density)
        xs = [(random.random()*1.2 - .1) * (max_x - min_x) + min_x for _ in range (num_starts)]
        ys = [(random.random()*1.2 - .1) * (max_y - min_y) + min_y for _ in range (num_starts)]
        field = util.NoiseField(complex(freq, freq), 0+0j, 0+0j, 0+0j)
        bg = field.paths(
            xs,
            ys,
            length,
            step_size,
            max_understep=0.5,
            clearance=self.pen_width/10/4,
            min_length=min_length,
        )
        self.vsk.stroke(2)
        self.vsk.geometry(fill_union.intersection(so.unary_union(bg)))
        # vsk.stroke(3)
        # vsk.geometry(so.unary_union(bg))


    def walk(self, vsk: Vsketch) -> None:
        if self.bubbles:
            shape = g.Point(0, 0).buffer(math.sqrt(3) / 2)
        else:
            shape = a.rotate(util.regular_polygon(6, 0+1j), 90)
        branches = [1+0j, rotation(math.pi/3), rotation(-math.pi/3)]
        branch_probs = [self.forward_prob, self.branch_prob, self.branch_prob]
        layer_scale = 0.5
        margin = -0.001

        debug = False

        start_directions = util.polygon_vertices(complex(0, math.sqrt(3)), 6)
        start_positions = [0+0j]

        result = [shape]

        vsk.scale(self.scale)

        todo = list(itertools.product(start_positions, start_directions, [0], [self.fuel]))
        while todo:
            x, v, level, fuel = todo.pop(0)
            prev = x
            x += v

            # should we drop down a layer?
            if random.random() < self.layer_prob:
                level += 1
                x += v * self.inset(v)
                v *= layer_scale
            scale = math.pow(layer_scale, level)

            if level > self.max_levels:
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
            for branch, prob in util.shuffle(zip(branches, branch_probs)):
                if random.random() < prob:
                    todo.append((x, v*branch, level, fuel-1))

        to_flow_fill = []
        for p in result:
            if self.multi_stroke:
                stroke = max(1, round(p.boundary.length / math.sqrt(2)))
            else:
                stroke = 1
            # do manual stroke weight to make sure we are only on the inside of the shape
            offset = self.pen_width/10/2 / self.scale
            for i in range(stroke):
                vsk.geometry(p.buffer(-self.gap-(i*offset)))
            if random.random() < self.fill_prob:
                if self.fill == "solid":
                    vsk.fill(2)
                    vsk.geometry(p.buffer(-self.gap-(stroke*offset)))
                    vsk.noFill()
                elif self.fill == "flow":
                    to_flow_fill.append(p.buffer(-self.gap-(stroke*offset)))

        if to_flow_fill:
            self.flow_fill(to_flow_fill)


    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.centered = False
        # smaller to make the fill look good
        vsk.penWidth(f"{self.pen_width/2}mm")

        self.walk(vsk)

        layout = f"layout {self.page_size} translate -- 0 -{self.offset}cm"
        pen = f"penwidth {self.pen_width}mm color black color -l2 blue"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt")


if __name__ == "__main__":
    HexGridSketch.display()
