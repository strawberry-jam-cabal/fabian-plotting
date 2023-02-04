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


VERTICES = {
    "ace": p.ace,
    "duce": p.duce,
    "star": p.star,
    "sun": p.sun,
    "jack": p.jack,
    "queen": p.queen,
    "king": p.king,
}

class PenroseSketch(vsketch.SketchClass):
    page_size = Param("4.5inx6.25in", choices=["11inx15in", "8.5inx11in", "6inx9in", "4.5inx6.25in"])
    scale = Param(1.0)
    pen_width_mm = Param(0.45)

    vertex = Param("ace", choices=VERTICES.keys())
    size = Param(5)
    angle = Param(0)
    iterations = Param(2)
    head_width = Param(0.04)
    tail_width = Param(0.02)


    def arc(self, arc, resolution: int = 24):
        (center, vector, angle) = arc
        num = round(abs(angle) * 2 / math.pi * resolution)
        step_angle = angle / num
        step = complex(math.cos(step_angle), math.sin(step_angle))
        current = vector
        result = [center + current]
        for _ in range(num):
            current *= step
            result.append(center + current)
        return g.LineString([(p.real, p.imag) for p in result])


    def draw_tri_arcs(self, tri, resolution=24, nose_color=2, tail_color=3):
        prev_stroke = self.vsk._cur_stroke
        [nose, tail] = tri.arcs()
        self.vsk.stroke(nose_color)
        self.vsk.geometry(self.arc(nose, resolution=resolution))
        self.vsk.stroke(tail_color)
        self.vsk.geometry(self.arc(tail, resolution=resolution))
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


    def outline(self, tiles: list[p.GoldenTriangle]):
        ps = [g.Polygon([(c.real, c.imag) for c in t.points()]) for t in tiles]
        join = g.JOIN_STYLE.mitre
        return so.unary_union([p.buffer(0.001, join_style=join) for p in ps]).buffer(-0.001, join_style=join)


    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.scale(self.scale)
        vsk.centered = False

        # tiles = p.ace(size=5)
        # vsk.stroke(4)
        # # [self.draw_tri(t) for t in tiles]
        # self.draw_outline(tiles)
        # vsk.stroke(1)
        # # vsk.stroke(2)
        # # [self.draw_tri(t) for k in tiles for t in k.decompose()]
        # # vsk.stroke(3)
        # [[self.draw_tri_arcs(t), self.draw_tri(t)] for k in tiles for t1 in k.decompose() for t in t1.decompose()]
        # # vsk.stroke(2)
        # # [[self.draw_tri_arcs(t, tail_color=2), self.draw_tri(t)] for k in tiles for t1 in k.decompose() for t2 in t1.decompose() for t in t2.decompose()]

        ##### With offset #####s
        start = VERTICES[self.vertex](size=self.size, angle=math.radians(self.angle))
        outline = self.outline(start)
        decomposed = start
        for _ in range(self.iterations):
            decomposed = [new for t in decomposed for new in t.decompose()]
        tiles = [g.LineString([(c.real, c.imag) for c in tile.points()[:3]]) for tile in decomposed]
        tile_size = decomposed[0].size
        head_arcs = so.unary_union([self.arc(tile.arcs()[0]) for tile in decomposed])
        tail_arcs = so.unary_union([self.arc(tile.arcs()[1]) for tile in decomposed])
        arcs = so.unary_union(
            [
                head_arcs.buffer(tile_size * self.head_width, cap_style=g.CAP_STYLE.round),
                tail_arcs.buffer(tile_size * self.tail_width, cap_style=g.CAP_STYLE.round),
            ]
        ).intersection(outline)

        vsk.stroke(1)
        vsk.geometry(outline)
        vsk.stroke(4)
        [vsk.geometry(x) for x in tiles]
        vsk.stroke(2)
        vsk.geometry(arcs)
        # vsk.geometry(head_arcs.buffer(decomposed[0].size * self.head_width, cap_style=g.CAP_STYLE.round).intersection(outline))
        # vsk.stroke(3)
        # vsk.geometry(tail_arcs.buffer(decomposed[0].size * self.tail_width, cap_style=g.CAP_STYLE.round).intersection(outline))

        layout = f"layout --landscape {self.page_size}"
        pen = f"penwidth {self.pen_width_mm}mm color #606060 color -l2 #C00060 color -l3 #0060C0"
        vsk.vpype(f"{layout} {pen} linemerge linesort --two-opt")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt linesimplify -t0.01mm")


if __name__ == "__main__":
    PenroseSketch.display()
