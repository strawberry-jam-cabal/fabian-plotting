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


class StrokeTestSketch(vsketch.SketchClass):
    page_size = Param("4.5inx6.25in", choices=["11inx15in", "8.5inx11in", "6inx9in", "4.5inx6.25in"])
    scale = Param(1.0)
    pen_width_mm = Param(0.45)
    line_width = Param(1.0)
    shells = Param(2)
    cap_length = Param(1/3)

    def stroke_path(self, path: g.LineString):
        polys = [
            stroke.sine_caps_stroke(
                path,
                self.line_width * (i + 1) / (self.shells + 1),
                path.length * self.cap_length,
            )
            for i in range(self.shells + 1)
        ]

        filled = util.concentric_fill(polys[0], self.pen_width_mm/10/2/self.scale)
        shells = [poly.boundary for poly in polys[1:]]
        self.vsk.geometry(so.unary_union(filled + shells))

    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.scale(self.scale)
        vsk.centered = False
        vsk.penWidth(f"{self.pen_width_mm/2}mm")

        arc = a.scale(util.arc(math.pi / 2, 3 * math.pi / 2, resolution=32), 4, 4, origin=(0, 0))
        arc2 = a.scale(arc, -1, 1, origin=(0, 0))

        self.stroke_path(arc)
        self.stroke_path(arc2)

        layout = f"layout {self.page_size}"
        pen = f"penwidth {self.pen_width_mm}mm color black color -l2 #C00060 color -l3 #0060C0"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt linesimplify -t0.01mm")


if __name__ == "__main__":
    StrokeTestSketch.display()
