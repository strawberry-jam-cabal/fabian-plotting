import pathlib
import sys
import math

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

        # right = p.GoldenTriangle(0j, 0, 6, True, join_right=True)
        # self.draw_tri(right)
        # vsk.stroke(2)
        # [self.draw_tri(tri) for tri in right.decompose()]

        # kite = p.kite(size=6)
        # [self.draw_tri(t) for t in kite]
        # vsk.stroke(2)
        # [self.draw_tri(t) for k in kite for t in k.decompose()]

        # t = p.GoldenTriangle(0j, 0, 6, False, join_right=True)
        # self.draw_tri(t)
        # vsk.stroke(2)
        # [self.draw_tri(t) for t in t.decompose()]

        # dart = p.dart(size=6)
        # [self.draw_tri(t) for t in dart]
        # vsk.stroke(2)
        # [self.draw_tri(t) for d in dart for t in d.decompose()]


        # kite = p.kite(angle=math.radians(-90), size=6)
        # [self.draw_tri(t) for t in kite]
        # vsk.stroke(2)
        # [self.draw_tri(t) for k in kite for t in k.decompose()]
        # vsk.stroke(3)
        # [self.draw_tri(t) for k in kite for t1 in k.decompose() for t in t1.decompose()]

        tiles = p.sun(size=5)
        [self.draw_tri(t) for t in tiles]
        vsk.stroke(2)
        [self.draw_tri(t) for k in tiles for t in k.decompose()]
        vsk.stroke(3)
        [self.draw_tri(t) for k in tiles for t1 in k.decompose() for t in t1.decompose()]


        layout = f"layout --landscape {self.page_size}"
        pen = f"penwidth {self.pen_width_mm}mm color black color -l2 #C00060 color -l3 #0060C0"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt linesimplify -t0.01mm")


if __name__ == "__main__":
    PenroseSketch.display()
