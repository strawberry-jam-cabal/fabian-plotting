import dataclasses
import itertools
import math
import random
from typing import Iterable, Tuple, TypeVar

import numpy as np
import pnoise
import shapely.geometry as g

T = TypeVar("T")

def polygon_vertices(start: complex, sides: int) -> list[complex]:
    """Vertices of a polygon centered at (0, 0).

    Args:
        start (complex): The first vertex of the polygon
        sides (int): The number of sides the polygon has

    Returns:
        list[complex]: The list of all the vertices
    """
    angle = 2*math.pi / sides
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
    num = round((stop - start) * 2/math.pi * resolution)
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


@dataclasses.dataclass
class LineTree:
    line: g.LineString
    children: list[Tuple["LineTree", float]]


class NoiseField():
    """A 2D noise field generated from two independent Perlin noise samples."""
    def __init__(self, frequency: complex, offset: complex, center: complex, attraction: complex) -> None:
        self.x_field = pnoise.Noise()
        self.y_field = pnoise.Noise()
        self.frequency = frequency
        self.offset = offset
        self.center = center
        self.attraction = attraction

    def get_values(self, xs: np.ndarray, ys: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        zeros = np.zeros_like(xs)
        scaled_xs = (xs - self.offset.real) * self.frequency.real
        scaled_ys = (ys - self.offset.imag) * self.frequency.imag
        vxs = self.x_field.perlin(scaled_xs, scaled_ys, zeros, grid_mode=False) * 2 - 1
        vys = self.y_field.perlin(scaled_xs, scaled_ys, zeros, grid_mode=False) * 2 - 1
        return (
            vxs + (xs - self.center.real) * -self.attraction.real,
            vys + (ys - self.center.imag) * -self.attraction.imag,
        )

    def understep(self, step_size: float, max_understep: float) -> float:
        return step_size * (1 - random.random() * max_understep)

    def paths(
        self,
        x_starts: list[float],
        y_starts: list[float],
        length: float,
        step_size: float,
        max_understep: float,
        clearance: float,
        min_length: float,
    ) -> list[g.LineString]:
        assert len(x_starts) == len(y_starts)

        hash_point = lambda p: (int(p.real/clearance), int(p.imag/clearance))

        @dataclasses.dataclass
        class Line:
            points: list[complex]
            fuel: float
            children: list["Line"]

        lines = [Line([complex(x, y)], length, []) for x, y in zip(x_starts, y_starts)]
        occupied = {hash_point(line.points[0]): (line, line.fuel) for line in lines}

        while any(line.fuel > 0 for line in lines):
            indices = [i for i in range(len(lines)) if lines[i].fuel > 0]
            xs = np.array([lines[i].points[-1].real for i in indices])
            ys = np.array([lines[i].points[-1].imag for i in indices])
            vxs, vys = self.get_values(xs, ys)
            step_sizes = np.array([self.understep(step_size, max_understep) for _ in range(len(xs))])
            vxs = np.multiply(vxs, step_sizes)
            vys = np.multiply(vys, step_sizes)
            xs = xs + vxs
            ys = ys + vys

            for i, x, y in zip(indices, xs, ys):
                point = complex(x, y)
                line = lines[i]
                line.fuel -= max(0.1, abs(line.points[-1] - point))
                h = hash_point(point)
                if h in occupied and occupied[h][0] != line:
                    (other, other_fuel) = occupied[h]
                    fuel_diff = line.fuel - other_fuel
                    if fuel_diff > 0:
                        other.fuel += fuel_diff
                        occupied[h] = (other, line.fuel)
                        line.fuel = 0
                        line.points.append(point)
                        other.children.append(line)
                else:
                    line.points.append(point)
                    occupied[h] = (line, line.fuel)

        # TODO: construct the DAG lines from the child pointers
        # heads = [line for line in lines if line.children]

        result = []
        for line in lines:
            if len(line.points) > 1:
                ls = g.LineString((p.real, p.imag) for p in line.points)
                if ls.length >= min_length:
                    result.append(ls)
        return result
