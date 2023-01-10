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


# def arc(start: float, stop: float, resolution: float = 16) -> g.LineString:
#     # res is number of points in a quarter circle
#     while stop < start:
#         stop += math.pi * 2
#     num = round((stop - start) * 2 / math.pi * resolution)
#     angles = np.linspace(start, stop, num)
#     x = np.cos(angles)
#     y = np.sin(angles)
#     return g.LineString(np.column_stack([x, y]))

class PenroseSketch(vsketch.SketchClass):
    page_size = Param("4.5inx6.25in", choices=["11inx15in", "8.5inx11in", "6inx9in", "4.5inx6.25in"])
    scale = Param(1.0)
    pen_width_mm = Param(0.45)


    def draw_arc(self, arc, resolution: int = 24):
        (center, vector, angle) = arc
        num = round(abs(angle) * 2 / math.pi * resolution)
        step_angle = angle / num
        step = complex(math.cos(step_angle), math.sin(step_angle))
        current = vector
        result = [center + current]
        for _ in range(num):
            current *= step
            result.append(center + current)
        self.vsk.geometry(g.LineString([(p.real, p.imag) for p in result]))


    def draw_tri_arcs(self, tri, resolution=24, nose_color=2, tail_color=3):
        prev_stroke = self.vsk._cur_stroke
        [nose, tail] = tri.arcs()
        self.vsk.stroke(nose_color)
        self.draw_arc(nose)
        self.vsk.stroke(tail_color)
        self.draw_arc(tail)
        if prev_stroke is None:
            self.vsk.noStroke()
        else:
            self.vsk.stroke(prev_stroke)


    def draw_tri(self, tri: p.GoldenTriangle):
        points = [(c.real, c.imag) for c in tri.points()]
        # self.vsk.strokeWeight(3)
        self.vsk.geometry(g.LineString(points[0:2]))
        self.vsk.geometry(g.LineString(points[1:3]))
        # self.vsk.strokeWeight(1)
        # self.vsk.geometry(g.Polygon([(c.real, c.imag) for c in tri.points()]))


    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.scale(self.scale)
        vsk.centered = False

        # right = p.GoldenTriangle(0j, 0, 6, True, join_right=True)
        # self.draw_tri(right)
        # vsk.stroke(2)
        # [self.draw_arc(a) for a in right.arcs()]
        # [self.draw_tri(tri) for tri in right.decompose()]

        # kite = p.kite(size=6)
        # [self.draw_tri(t) for t in kite]
        # vsk.stroke(2)
        # [self.draw_arc(a) for t in kite for a in t.arcs()]
        # [self.draw_tri(t) for k in kite for t in k.decompose()]

        # t = p.GoldenTriangle(0j, math.radians(36), 6, False, join_right=True)
        # self.draw_tri(t)
        # vsk.stroke(2)
        # [self.draw_arc(a) for a in t.arcs()]
        # [self.draw_tri(t) for t in t.decompose()]

        # dart = p.dart(size=6)
        # [self.draw_tri(t) for t in dart]
        # vsk.stroke(2)
        # [self.draw_arc(a) for t in dart for a in t.arcs()]
        # [self.draw_tri(t) for d in dart for t in d.decompose()]

        # kite = p.kite(angle=math.radians(-90), size=6)
        # [self.draw_tri(t) for t in kite]
        # vsk.stroke(2)
        # [self.draw_tri(t) for k in kite for t in k.decompose()]
        # # vsk.stroke(2)
        # # [self.draw_arc(a) for k in kite for t in k.decompose() for a in t.arcs()]
        # vsk.stroke(3)
        # [self.draw_tri(t) for k in kite for t1 in k.decompose() for t in t1.decompose()]
        # vsk.stroke(4)
        # [self.draw_tri(t) for k in kite for t1 in k.decompose() for t2 in t1.decompose() for t in t2.decompose()]

        tiles = p.sun(size=5)
        # [self.draw_tri(t) for t in tiles]
        # vsk.stroke(2)
        # [self.draw_tri(t) for k in tiles for t in k.decompose()]
        # vsk.stroke(3)
        # [self.draw_tri(t) for k in tiles for t1 in k.decompose() for t in t1.decompose()]
        # vsk.stroke(2)
        [[self.draw_tri_arcs(t, tail_color=2), self.draw_tri(t)] for k in tiles for t1 in k.decompose() for t2 in t1.decompose() for t in t2.decompose()]

        layout = f"layout --landscape {self.page_size}"
        pen = f"penwidth {self.pen_width_mm}mm color #606060 color -l2 #C00060 color -l3 #0060C0"
        vsk.vpype(f"{layout} {pen} linemerge linesort --two-opt")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt linesimplify -t0.01mm")


if __name__ == "__main__":
    PenroseSketch.display()
