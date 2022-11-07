import itertools
import math

import vsketch
from vsketch import Param, Vsketch
import shapely.affinity as a
import shapely.geometry as g
import shapely.ops as so

import util


def rotation(angle: float) -> complex:
    """A rotation of the unit vector by the given angle in radians."""
    return complex(math.cos(angle), math.sin(angle))


def sin_style(line: g.LineString, max_width: float) -> g.Polygon:
    points = [complex(x, y) for x, y in line.coords]
    assert len(points) > 1

    left = 0+1j
    right = 0-1j

    length = line.length / math.pi
    dist = 0
    result = []

    prev_v = points[1] - points[0]
    for i in range(1, len(points) - 1):
        step = abs(prev_v)
        dist += step
        next_v = points[i+1] - points[i]
        v = prev_v/step + next_v/abs(next_v)
        v /= abs(v)
        width = math.sin(dist / length) * max_width / 2
        result.append((points[i] + v*width*right, points[i] + v*width*left))
        prev_v = next_v

    return g.Polygon(
        itertools.chain(
            [(points[0].real, points[0].imag)],
            ((r.real, r.imag) for r, _ in result),
            [(points[-1].real, points[-1].imag)],
            reversed(list((l.real, l.imag) for _, l in result)),
        )
    )


class StrokeTestSketch(vsketch.SketchClass):
    page_size = Param("4.5inx6.25in", choices=["11inx15in", "8.5inx11in", "6inx9in", "4.5inx6.25in"])
    scale = Param(1.0)
    pen_width = Param(0.45)
    line_width = Param(1.0)

    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.scale(self.scale)
        vsk.centered = False
        vsk.penWidth(f"{self.pen_width/2}mm")

        arc = a.scale(util.arc(math.pi / 2, 3 * math.pi / 2, resolution=32), 4, 4, origin=(0, 0))

        vsk.geometry(
            so.unary_union(
                util.concentric_fill(
                    sin_style(arc, self.line_width),
                    self.pen_width/10/2,
                )
            )
        )

        layout = f"layout {self.page_size}"
        pen = f"penwidth {self.pen_width}mm color black color -l2 #C00060 color -l3 #0060C0"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt linesimplify -t0.01mm")


if __name__ == "__main__":
    StrokeTestSketch.display()
