import dataclasses
import itertools
import math
import random
from typing import Iterable, Tuple, TypeVar

import numpy as np
import pnoise
import shapely.geometry as g
import shapely.validation as sv

from noise_field import NoiseField, points_within

T = TypeVar("T")


def polygon_vertices(start: complex, sides: int) -> list[complex]:
    """Vertices of a polygon centered at (0, 0).

    Args:
        start (complex): The first vertex of the polygon
        sides (int): The number of sides the polygon has

    Returns:
        list[complex]: The list of all the vertices
    """
    angle = 2 * math.pi / sides
    r = complex(math.cos(angle), math.sin(angle))
    return [start * r**i for i in range(sides)]


def regular_polygon(sides: int, vertex: complex = 0+1j) -> g.Polygon:
    """A regular polygon centered at (0, 0).

    The vertex argument can be used to create a larger or smaller polygon.

    Args:
        sides (int): The number of sides the polygon has
        vertex (complex, optional): A vertex of the polygon. Defaults to 0+1j.

    Returns:
        g.Polygon
    """
    return g.Polygon((c.real, c.imag) for c in polygon_vertices(vertex, sides))


def arc(start: float, stop: float, resolution: float = 16) -> g.LineString:
    # res is number of points in a quarter circle
    while stop < start:
        stop += math.pi * 2
    num = round((stop - start) * 2 / math.pi * resolution)
    angles = np.linspace(start, stop, num)
    x = np.cos(angles)
    y = np.sin(angles)
    return g.LineString(np.column_stack([x, y]))


def pie_slice(start: float, stop: float, resolution: float = 16) -> g.Polygon:
    return g.Polygon(itertools.chain([(0, 0)], arc(start, stop, resolution).coords))


def shuffle(xs: Iterable[T]) -> list[T]:
    """A shuffled copy of an iterable."""
    res = list(xs)
    random.shuffle(res)
    return res


def concentric_fill(
    poly: g.Polygon | g.MultiPolygon, step: float
) -> list[g.LinearRing]:
    """Fills in a polygon by recursively adding buffers to the result line collection."""
    if not poly.is_valid:
        valid = sv.make_valid(poly)
        return concentric_fill(valid, step)

    if poly.geom_type == "MultiPolygon":
        return [ring for part in poly.geoms for ring in concentric_fill(part, step)]
    elif poly.geom_type == "Polygon":
        if len(poly.exterior.coords) > 1:
            return (
                [poly.exterior]
                + list(poly.interiors)
                + concentric_fill(poly.buffer(-step), step)
            )
        else:
            return []
    else:
        raise RuntimeError(f"Unsupported geometry: {poly.geom_type}")
