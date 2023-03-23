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


class FlowSketch(vsketch.SketchClass):
    # Sketch parameters:
    page_size = Param("6inx9in", choices=["8.5inx11in", "6inx9in", "6inx8in", "4.5inx6.25in", "4inx5.5in", "2.5inx3.75in"])
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

    def gen_hairs(self, vsk: Vsketch) -> None:
        crop = g.box(0, 0, self.width, self.height)

        (min_x, min_y, max_x, max_y) = crop.bounds
        num_starts = round((max_x - min_x) * (max_y - min_y) * self.density)
        xs = [(random.random()*1.2 - .1) * (max_x - min_x) + min_x for _ in range (num_starts)]
        ys = [(random.random()*1.2 - .1) * (max_y - min_y) + min_y for _ in range (num_starts)]

        field = util.NoiseField(
            frequency=complex(self.frequency, self.frequency),
            offset=0+0j,
            center=complex(
                self.width/2,
                # self.width/2,
                # 0,
                -self.width*2,
            ),
            attraction=0.0+.015j
        )

        starts = util.points_within(a.scale(crop, 1.2, 1.2), self.density)
        xs = [x for p in starts.geoms for x, _ in p.coords]
        ys = [y for p in starts.geoms for _, y in p.coords]
        args = dict(x_starts=xs, y_starts=ys, length=self.fuel, max_understep=0.5, clearance=self.pen_width/10/2, min_length=self.min_length)
        forward = field.paths(step_size=self.detail, **args)
        backward = field.paths(step_size=-self.detail, **args)
        # bg = forward + backward

        # bg = field.paths(
        #     xs, ys, self.fuel, self.detail, 0.5, self.pen_width/10/2, self.min_length
        # )

        circle = lambda r: g.Point(0, 0).buffer(r)
        ring = lambda a, b: circle(a).difference(circle(b))
        scale_and_center = lambda s: a.translate(a.scale(s, self.width*0.45, -self.width*0.45, origin=(0, 0)), self.width/2, self.width/2)
        # shape = a.translate(a.scale(ring(1, 0.95).union(ring(.9, .8)).union(ring(.75, .7)).union(ring(.55, .45)).union(ring(.35, 0)), self.width*.45, self.width*.45), self.width/2, self.height/2)
        # shape = a.translate(a.scale(util.regular_polygon(6), self.width * 0.6, self.width * 0.6), self.width/2, self.height/2)
        shape = a.translate(a.scale(g.Point(0, 0).buffer(1), self.width * 0.5, self.height * 0.5), self.width/2, self.height/2)
        crop = crop.intersection(shape)
        # vsk.geometry(crop.intersection(so.unary_union(bg)))
        vsk.geometry(crop.intersection(so.unary_union(forward)))
        # vsk.stroke(2)
        vsk.geometry(crop.intersection(so.unary_union(backward)))

        # masks = [
        #     (scale_and_center(a.rotate(util.pie_slice(0, 3).intersection(ring(1, .95)), -60, origin=(0, 0))), 1),
        #     (scale_and_center(a.rotate(util.pie_slice(0, 3).intersection(ring(.9, .8)), 30, origin=(0, 0))), 1),
        #     (scale_and_center(a.rotate(util.pie_slice(0, 4).intersection(ring(.75, .55)), 120, origin=(0, 0))), 2),
        #     (scale_and_center(a.rotate(util.pie_slice(0, 4).intersection(ring(.5, .2)), 30, origin=(0, 0))), 3),
        # ]
        # for mask, layer in masks:
        #     vsk.stroke(layer)
        #     vsk.geometry(mask.intersection(so.unary_union(bg)))

    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.scale(self.scale)
        vsk.centered = False
        vsk.penWidth(f"{self.pen_width/2}mm")

        self.gen_hairs(vsk)

        layout = f"layout {self.page_size} translate -- 0 -{self.offset}cm"
        pen = f"penwidth {self.pen_width}mm color black color -l2 #C00060 color -l3 #0060C0"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt linesimplify -t0.01mm")


if __name__ == "__main__":
    FlowSketch.display()
