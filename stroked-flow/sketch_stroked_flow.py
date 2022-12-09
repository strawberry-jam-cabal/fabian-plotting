import math
import pathlib
import sys

import vsketch
from vsketch import Param, Vsketch
import shapely.affinity as a
import shapely.geometry as g
import shapely.ops as so

sys.path.append(str(pathlib.Path(__file__).parent.parent))
import util
import stroke


class StrokedFlowSketch(vsketch.SketchClass):
    page_size = Param("4.5inx6.25in", choices=["11inx15in", "8.5inx11in", "6inx9in", "4.5inx6.25in"])
    scale = Param(1.0)
    pen_width_mm = Param(0.45)

    width = Param(10.0)
    height = Param(14.0)

    stroke_width = Param(0.12)

    density = Param(1.4)
    fuel = Param(3.0)
    min_length = Param(0.0)
    frequency = Param(0.35)
    detail = 0.25
    max_understep = 0.5


    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.scale(self.scale)
        vsk.centered = False
        vsk.penWidth(f"{self.pen_width_mm/2}mm")

        crop = g.box(0, 0, self.width, self.height)

        lines = util.NoiseField(
            complex(self.frequency, self.frequency),
            0+0j,
            complex(self.width/2, self.width/2),
            # .1+.1j,
            0j,
        ).paths_in_polygon(
            a.scale(crop, 1.2, 1.2), self.density, self.fuel, self.detail, self.max_understep, self.pen_width_mm/10/2, self.min_length
        )

        vsk.geometry(
            so.unary_union(
                util.concentric_fill(
                    poly=so.unary_union([stroke.sine_caps_stroke(line, self.stroke_width, 1) for line in lines]).intersection(crop),
                    step=self.pen_width_mm/10/2/self.scale,
                )
            )
        )

        # vsk.geometry(so.unary_union(lines).intersection(crop))

        layout = f"layout {self.page_size}"
        pen = f"penwidth {self.pen_width_mm}mm color black color -l2 #C00060 color -l3 #0060C0"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt linesimplify -t0.01mm")


if __name__ == "__main__":
    StrokedFlowSketch.display()
