import pathlib
import sys

import shapely.affinity as a
import shapely.geometry as g
import shapely.ops as so
import vsketch
from vsketch import Param, Vsketch

sys.path.append(str(pathlib.Path(__file__).parent.parent))
import fabiangeneral.penrose as p


class PenroseSketch(vsketch.SketchClass):
    page_size = Param("4.5inx6.25in", choices=["11inx15in", "8.5inx11in", "6inx9in", "4.5inx6.25in"])
    scale = Param(1.0)
    pen_width_mm = Param(0.45)


    def draw_tri(self, tri: p.GoldenTriangle):
        self.vsk.geometry(g.Polygon([(c.real, c.imag) for c in tri.points()]))


    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.scale(self.scale)
        vsk.centered = False

        [self.draw_tri(tri) for tri in p.kite()]
        [self.draw_tri(tri.translate(2+0j)) for tri in p.dart()]

        layout = f"layout --landscape {self.page_size}"
        pen = f"penwidth {self.pen_width_mm}mm color black color -l2 #C00060 color -l3 #0060C0"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt linesimplify -t0.01mm")


if __name__ == "__main__":
    PenroseSketch.display()
