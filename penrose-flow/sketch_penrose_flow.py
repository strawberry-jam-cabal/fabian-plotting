import pathlib
import random
import sys
import math

import shapely.affinity as a
import shapely.geometry as g
import shapely.ops as so
import vsketch
from vsketch import Param, Vsketch

sys.path.append(str(pathlib.Path(__file__).parent.parent))
import fabiangeneral.penrose as p
import util


class PenroseFlowSketch(vsketch.SketchClass):
    page_size = Param("4.5inx6.25in", choices=["11inx15in", "8.5inx11in", "6inx9in", "4.5inx6.25in"])
    scale = Param(1.0)
    pen_width_mm = Param(0.45)

    vertex = Param("ace", choices=p.VERTICES.keys())
    size = Param(5)
    angle = Param(0)
    iterations = Param(2)
    spacing = Param(0.1)

    density = Param(6.0)
    fuel = Param(3.0)
    min_length = Param(0.0)
    frequency = Param(0.35)
    detail = Param(0.25)


    def outline(self, tiles: list[p.GoldenTriangle]) -> g.Polygon:
        ps = [g.Polygon([(c.real, c.imag) for c in t.points()]) for t in tiles]
        join = g.JOIN_STYLE.mitre
        return so.unary_union([p.buffer(0.001, join_style=join) for p in ps]).buffer(-0.001, join_style=join)


    def flow_field(self, bounds: g.Polygon) -> list[g.LineString]:
        start_points = util.points_within(bounds.buffer(self.fuel / 4 / self.detail), self.density)
        xs = [point.x for point in start_points.geoms]
        ys = [point.y for point in start_points.geoms]

        (minx, miny, maxx, maxy) = bounds.bounds
        center = complex((minx + maxx) / 2, (miny + maxy) / 2)

        return util.NoiseField(
            frequency=complex(self.frequency, self.frequency),
            offset=0+0j,
            center=center,
            attraction=0.1 + 0.1j,
        ).paths(
            x_starts=xs,
            y_starts=ys,
            length=self.fuel,
            step_size=self.detail,
            max_understep=0.5,
            clearance=self.pen_width_mm / 10 / 2,
            min_length=self.min_length,
        )



    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.scale("cm")
        vsk.scale(self.scale)
        vsk.centered = False

        start = p.VERTICES[self.vertex](size=self.size, angle=math.radians(self.angle))
        outline = self.outline(start)
        decomposed = start
        for _ in range(self.iterations):
            decomposed = [new for t in decomposed for new in t.decompose()]

        tiles = [g.LineString([(c.real, c.imag) for c in tile.points()[:3]]) for tile in decomposed]

        spaces = so.unary_union(tiles).union(outline.boundary).buffer(self.spacing)
        spaced = outline.difference(spaces)
        vsk.stroke(1)
        vsk.geometry(spaced)

        # vsk.stroke(2)
        lines = so.unary_union(self.flow_field(outline))
        vsk.geometry(lines.intersection(spaced.buffer(-self.pen_width_mm/10/4)))


        layout = f"layout --landscape {self.page_size}"
        # pen = f"penwidth {self.pen_width_mm}mm color #606060 color -l2 #C00060 color -l3 #0060C0"
        pen = f"penwidth {self.pen_width_mm}mm color black"
        vsk.vpype(f"{layout} {pen} linemerge linesort --two-opt")


    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt linesimplify -t0.01mm")


if __name__ == "__main__":
    PenroseFlowSketch.display()
