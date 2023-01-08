import random

import numpy as np
import shapely.affinity as a
import shapely.geometry as g
import shapely.ops as so
import vsketch
from vsketch import Param, Vsketch

import noise_field


class WrappedSketch(vsketch.SketchClass):
    page_size = Param("6inx9in", choices=["11inx15in", "8.5inx11in", "6inx9in", "4.5inx6.25in", "2.5inx3.75in"])
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

        field = noise_field.WrappedNoiseField(
            frequency=complex(self.frequency, self.frequency),
            offset=0+0j,
            x_wrap=(0.0, self.width),
            y_wrap=(0.0, self.height),
        )
        bg = field.paths(
            xs, ys, self.fuel, self.detail, self.max_understep, self.pen_width/10/2, self.min_length
        )

        vsk.geometry(crop.intersection(so.unary_union(bg)))

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
    WrappedSketch.display()
