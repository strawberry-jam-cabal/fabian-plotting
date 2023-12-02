import itertools
import math
import pathlib
import random
import sys


import shapely.affinity as a
import shapely.geometry as g
import shapely.ops as so
import vsketch
from vsketch import Param, Vsketch

sys.path.append(str(pathlib.Path(__file__).parent.parent))
import util


class SquareGridSketch(vsketch.SketchClass):
    # Sketch parameters:
    page_size = Param("4.5inx6.5in", choices=["11inx15in", "8.5inx11in", "6inx9in", "4.5inx6.25in"])
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

    fill = Param("flow", choices=["flow", "solid", "none"])
    bubbles = Param(False)
    multi_stroke = Param(True)


    def walk(self, vsk: Vsketch) -> None:
        shape = util.regular_polygon(4, 0+1j)
        inset = [-0.25+0.25j, -0.25-0.25j]
        branches = [1+0j, 0+1j, 0-1j]
        branch_probs = [self.forward_prob, self.branch_prob, self.branch_prob]
        layer_scale = 0.5
        margin = -0.001

        debug = False

        start_directions = util.polygon_vertices(1+1j, 4)
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
            for branch, prob in util.shuffle(zip(branches, branch_probs)):
                if random.random() < prob:
                    todo.append((x, v*branch, scale, fuel-1))

        to_fill = []
        for p in result:
            if self.bubbles:
                inscribe_radius = p.boundary.length / 8
                # shrink = min(p.boundary.length / 8, .25)
                # shrink = .25
                shrink = 1
                if shrink >= inscribe_radius:
                    p = p.centroid.buffer(inscribe_radius, quad_segs=8)
                else:
                    p = p.buffer(-shrink).buffer(shrink, quad_segs=8)
            if self.multi_stroke:
                stroke = max(1, round(p.boundary.length / math.sqrt(2)))
            else:
                stroke = 1
            # do manual stroke weight to make sure we are only on the inside of the shape
            offset = self.pen_width/10/2 / self.scale
            border_points = []
            for i in range(stroke):
                border_points.extend(p.buffer(-self.gap-(i*offset)).boundary.coords)
                # vsk.geometry(p.buffer(-self.gap-(i*offset)))
            vsk.geometry(g.LineString(border_points))
            if random.random() < self.fill_prob:
                if self.fill == "solid":
                    vsk.fill(2)
                    # vsk.geometry(p.buffer(-self.gap))
                    vsk.geometry(p.buffer(-self.gap-(stroke*offset)))
                    vsk.noFill()
                elif self.fill == "flow":
                    to_fill.append(p.buffer(-self.gap-(stroke*offset)))

        if to_fill:
            # Fill Params
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
            vsk.stroke(2)
            vsk.geometry(fill_union.intersection(so.unary_union(bg)))
            # vsk.stroke(3)
            # vsk.geometry(so.unary_union(bg))


    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.centered = False
        vsk.penWidth(f"{self.pen_width/2}mm")

        self.walk(vsk)

        # --landscape on the layout command
        layout = f"layout {self.page_size} translate -- 0 -{self.offset}cm"
        pen = f"penwidth {self.pen_width}mm color black color -l2 blue"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt")


if __name__ == "__main__":
    SquareGridSketch.display()
