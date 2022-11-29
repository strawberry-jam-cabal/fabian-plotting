import pathlib
import random
import sys
from typing import overload

import vsketch
from vsketch import Param, Vsketch
import shapely.affinity as a
import shapely.geometry as g
import shapely.ops as so
import shapely.geometry.base as gb
import numpy as np

sys.path.append(str(pathlib.Path(__file__).parent.parent))
import util


@overload
def sample(geom: g.MultiLineString, resolution: float) -> g.MultiLineString: ...
def sample(geom: g.LineString, resolution: float) -> g.LineString:
    if geom.geom_type == "MultiLineString":
        return g.MultiLineString(sample(part) for part in geom.geoms)

    if geom.geom_type != "LineString":
        raise RuntimeError(f"Unsupported geometry {geom.geom_type}")

    points = []
    start = geom.coords[0]
    for end in geom.coords[1:]:
        line = g.LineString([start, end])
        count = round(line.length / resolution)
        points.extend(line.interpolate(t, normalized=True) for t in np.linspace(0, 1, count, endpoint=False))
        start = end
    points.append(geom.coords[-1])

    return g.LineString(points)


def circle_from_points(points: list[complex], resolution: int = 16) -> g.Polygon:
    """Create a circle with the given points on the boundary.

    Args:
        points: The points on the boundary of the circle. Should contain two or three elements.
        resolution: The resolution of the polygon. Defaults to 16.

    Raises:
        RuntimeError: If there are not the right number of points on the boundary

    Returns:
        A circle polygon
    """
    if len(points) not in [2, 3]:
        raise RuntimeError(f"Cannot define cirlce from {points}")
    center = circle_center(points)
    return g.Point(center.real, center.imag).buffer(abs(points[0] - center), resolution)


def circle_center(edge_points: list[complex]) -> complex:
    """Find the center of the smallest circle with the given points on the circle.

    Args:
        edge_points: Points on the circle. Cannot be empty or have more than 3 elements.

    Raises:
        RuntimeError: If there are 0 or more than 3 points in the given list

    Returns:
        The center point
    """
    match edge_points:
        case [a]:
            return a
        case [a, b]:
            return (a + b) / 2
        case [a, b, c]:
            a2 = a.real**2 + a.imag**2
            b2 = b.real**2 + b.imag**2
            c2 = c.real**2 + c.imag**2
            ab = a - b
            bc = b - c
            ca = c - a
            d = 2 * (a.real * bc.imag + b.real * ca.imag + c.real * ab.imag)
            x = (a2 * bc.imag + b2 * ca.imag + c2 * ab.imag) / d
            y = (a2 * -bc.real + b2 * -ca.real + c2 * -ab.real) / d
            return complex(x, y)
        case _:
            raise RuntimeError(f"Circle center not supported for {len(edge_points)} points")


def bounding_circle(geom: gb.BaseGeometry, resolution: int = 16) -> g.Polygon:
    """Returns the smallest circle containing all the points in the given geometry."""

    def point_in_circle(point: complex, edge_points: list[complex]) -> bool:
        """Check if a point is in a circle"""
        match edge_points:
            case []:
                return False
            case [a]:
                return a == point
            case [a, _] | [a, _, _]:
                center = circle_center(edge_points)
                return abs(point - center) < abs(a - center)
            case _:
                raise RuntimeError(f"Bounding circle over defined")

    def welzl(points: list[complex], edge_points: list[complex]) -> list[complex]:
        """Find the points that must be on the boundary of the minimal covering disk.
        See https://en.wikipedia.org/wiki/Smallest-circle_problem#Welzl's_algorithm
        """
        if not points or len(edge_points) == 3:
            return edge_points
        maybe = welzl(points[1:], edge_points)
        if point_in_circle(points[0], maybe):
            return maybe
        else:
            return welzl(points[1:], edge_points+[points[0]])

    # it shouldn't be necessary to run on the convex hull, but I'm skeptical about the
    # performance on a large number of points
    hull_points = list({complex(*p) for p in geom.convex_hull.boundary.coords})
    random.shuffle(hull_points)
    return circle_from_points(welzl(hull_points, []), resolution)


def points_within(p: g.Polygon | g.MultiPolygon, density: float) -> g.MultiPoint:
    """Generate random points within a polygon.

    Args:
        p: The bounding polygon
        density: The density of the points
    """
    (min_x, min_y, max_x, max_y) = p.bounds
    count = round(density * (max_x - min_x) * (max_y - min_y))
    points = g.MultiPoint([(random.uniform(min_x, max_x), random.uniform(min_y, max_y)) for _ in range(count)])
    return points.intersection(p)


def seven_peaks(scale: float) -> g.MultiLineString:
    distance = scale / 6
    vertices = list(util.polygon_vertices(0+1j*scale*2.5, 6))
    # vertices.append(0j)
    shape = g.Point(0, 0)
    # shape = g.MultiPoint([(p.real, p.imag) for p in vertices])
    shape = shape.buffer(distance, resolution=8)
    lines = []
    for _ in range(15):
        lines.append(shape.boundary.simplify(.001))
        shape = shape.buffer(distance, resolution=1)
        if vertices:
            new_point = vertices.pop()
            shape = shape.union(g.Point(new_point.real, new_point.imag).buffer(distance, resolution=8))
    return so.unary_union(lines)


class DistortSketch(vsketch.SketchClass):
    page_size = Param("4.5inx6.5in", choices=["11inx15in", "8.5inx11in", "6inx9in", "4.5inx6.25in"])
    offset = Param(0.0)
    pen_width = Param(0.3)
    scale = Param(1.0)

    freq = Param(0.25)
    steps = Param(20)

    x = Param(4)
    y = Param(4)
    rings = Param(6)

    density = Param(6.0)
    length = Param(1.0)
    padding = Param(0.5)

    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.centered = False
        vsk.penWidth(f"{self.pen_width/2}mm")

        field = util.NoiseField((1 + 1j) * self.freq / self.scale, 0+0j, 0+0j, 0+0j)

        # shapes = so.unary_union([
        #     g.Point(0, 0).buffer(r).boundary for r in range(1, 5)
        # ])

        start_shapes = []
        for x in range(self.x):
            for y in range(self.y):
                for r in range(1, self.rings):
                    start_shapes.append(g.Point(x*2.5*self.scale, y*2.5*self.scale).buffer(r/self.rings*self.scale).boundary)
        start_shapes = g.MultiLineString(start_shapes)

        start_shapes = seven_peaks(self.scale)

        shapes = field.distort(start_shapes, step_size=0.1, steps=self.steps)
        vsk.geometry(shapes)

        # for r in range(1, 6):
        #     line = util.regular_polygon(6, complex(0, r)).boundary
        #     vsk.geometry(field.distort(sample(line, 0.1), self.step_size, self.steps))

        # bounds = g.Polygon(field.distort(bounding_circle(start_shapes, resolution=64).buffer(self.padding * self.scale).boundary, .1, self.steps))
        # # bounds = a.scale(g.box(*start_shapes.bounds), 1.2, 1.2)
        # start_points = points_within(bounds.buffer(self.length * self.scale), self.density / self.scale**2)

        # lines = field.paths(
        #     [p.x for p in start_points.geoms],
        #     [p.y for p in start_points.geoms],
        #     length=self.length * self.scale,
        #     step_size=0.25,
        #     max_understep=0.5,
        #     clearance=self.pen_width/10/2,
        #     min_length=0
        # )

        # vsk.stroke(2)
        # inside = so.unary_union([g.Polygon(line) for line in shapes.geoms])
        # vsk.geometry(g.MultiLineString(lines).difference(inside).intersection(bounds))
        # vsk.strokeWeight(3)
        # vsk.geometry(bounds.buffer(self.padding * self.scale / 2))

        layout = f"layout --landscape {self.page_size} translate -- 0 -{self.offset}cm"
        pen = f"penwidth {self.pen_width}mm color black color -l2 blue"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("reloop linesort --two-opt")


if __name__ == "__main__":
    DistortSketch.display()
