import random
from typing import Tuple

import numpy as np
import shapely.affinity as a
import shapely.geometry as g
import shapely.ops as so
import vsketch
from vsketch import Param, Vsketch

import util


class WrappedNoiseField(util.NoiseField):
    def __init__(
        self,
        frequency: complex,
        offset: complex,
        x_wrap: Tuple[float, float] | None = None,
        y_wrap: Tuple[float, float] | None = None,
    ) -> None:
        super().__init__(frequency, offset, 0+0j, 0+0j)
        self.x_wrap = x_wrap
        self.y_wrap = y_wrap

    def get_values(self, xs: np.ndarray, ys: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        # move xs and ys to the right spot if we are wrapping them
        if self.x_wrap is not None:
            (x_min, x_max) = self.x_wrap
            x_span = x_max - x_min
            xs = np.mod(xs - x_min, x_span) + x_min
        if self.y_wrap is not None:
            (y_min, y_max) = self.y_wrap
            y_span = y_max - y_min
            ys = np.mod(ys - y_min, y_max - y_min) + y_min

        def mix(
            pos, neg, loc: np.ndarray, offset: float, span: float
        ) -> Tuple[np.ndarray, np.ndarray]:
            span_ratio = (loc - offset) / span
            (x_pos, y_pos) = pos
            (x_neg, y_neg) = neg
            return (
                np.multiply(1 - span_ratio, x_pos) + np.multiply(span_ratio, x_neg),
                np.multiply(1 - span_ratio, y_pos) + np.multiply(span_ratio, y_neg),
            )

        pos = super().get_values(xs, ys)

        if self.x_wrap is None and self.y_wrap is None:
            return pos
        if self.x_wrap is not None and self.y_wrap is None:
            x_neg = super().get_values(xs - x_span, ys)
            return mix(pos, x_neg, xs, x_min, x_span)
        elif self.y_wrap is not None and self.x_wrap is None:
            y_neg = super().get_values(xs, ys - y_span)
            return mix(pos, y_neg, ys, y_min, y_span)
        else:
            x_neg = super().get_values(xs - x_span, ys)
            y_neg = super().get_values(xs, ys - y_span)
            both_neg = super().get_values(xs - x_span, ys - y_span)
            return mix(
                mix(pos, x_neg, xs, x_min, x_span),
                mix(y_neg, both_neg, xs, x_min, x_span),
                ys,
                y_min,
                y_span
            )


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

        field = WrappedNoiseField(
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
