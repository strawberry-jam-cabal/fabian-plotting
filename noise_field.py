import dataclasses
import random

import numpy as np
import pnoise
import shapely.geometry as g


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


class NoiseField:
    """A 2D noise field generated from two independent Perlin noise samples."""

    def __init__(
        self, frequency: complex, offset: complex, center: complex, attraction: complex
    ) -> None:
        self.x_field = pnoise.Noise()
        self.y_field = pnoise.Noise()
        self.frequency = frequency
        self.offset = offset
        self.center = center
        self.attraction = attraction

    def get_values(
        self, xs: np.ndarray, ys: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
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

    def paths_in_polygon(
        self,
        poly: g.Polygon | g.MultiPolygon,
        density: float,
        length: float,
        step_size: float,
        max_understep: float,
        clearance: float,
        min_length: float,
    ) -> list[g.LineString]:
        starts = points_within(poly, density)
        return self.paths(
            [x for p in starts.geoms for x, _ in p.coords],
            [y for p in starts.geoms for _, y in p.coords],
            length,
            step_size,
            max_understep,
            clearance,
            min_length,
        )

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

        hash_point = lambda p: (int(p.real / clearance), int(p.imag / clearance))

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
            step_sizes = np.array(
                [self.understep(step_size, max_understep) for _ in range(len(xs))]
            )
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

    def distort(self, shape: g.LineString, step_size: float, steps: int) -> g.MultiLineString:
        if shape.geom_type == "MultiLineString":
            return g.MultiLineString([self.distort(line, step_size, steps) for line in shape.geoms])

        if shape.geom_type != "LineString":
            raise RuntimeError(f"Unsupported geometry type: {shape.geom_type}")

        shape.coords
        xs = np.array([x for x, _ in shape.coords])
        ys = np.array([y for _, y in shape.coords])
        for _ in range(steps):
            (vxs, vys) = self.get_values(xs, ys)
            vxs *= step_size
            vys *= step_size
            xs = xs + vxs
            ys = ys + vys

        return g.LineString(zip(xs, ys))


class WrappedNoiseField(NoiseField):
    def __init__(
        self,
        frequency: complex,
        offset: complex,
        x_wrap: tuple[float, float] | None = None,
        y_wrap: tuple[float, float] | None = None,
    ) -> None:
        super().__init__(frequency, offset, 0+0j, 0+0j)
        self.x_wrap = x_wrap
        self.y_wrap = y_wrap

    def get_values(self, xs: np.ndarray, ys: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        # move xs and ys to the right spot if we are wrapping them
        if self.x_wrap is not None:
            (x_min, x_max) = self.x_wrap
            x_span = x_max - x_min
            xs = np.mod(xs - x_min, x_span) + x_min
        if self.y_wrap is not None:
            (y_min, y_max) = self.y_wrap
            y_span = y_max - y_min
            ys = np.mod(ys - y_min, y_max - y_min) + y_min

        def mix(
            pos, neg, loc: np.ndarray, offset: float, span: float
        ) -> tuple[np.ndarray, np.ndarray]:
            span_ratio = (loc - offset) / span
            (x_pos, y_pos) = pos
            (x_neg, y_neg) = neg
            return (
                np.multiply(1 - span_ratio, x_pos) + np.multiply(span_ratio, x_neg),
                np.multiply(1 - span_ratio, y_pos) + np.multiply(span_ratio, y_neg),
            )

        pos = super().get_values(xs, ys)

        if self.x_wrap is None and self.y_wrap is None:
            return pos
        if self.x_wrap is not None and self.y_wrap is None:
            x_neg = super().get_values(xs - x_span, ys)
            return mix(pos, x_neg, xs, x_min, x_span)
        elif self.y_wrap is not None and self.x_wrap is None:
            y_neg = super().get_values(xs, ys - y_span)
            return mix(pos, y_neg, ys, y_min, y_span)
        else:
            x_neg = super().get_values(xs - x_span, ys)
            y_neg = super().get_values(xs, ys - y_span)
            both_neg = super().get_values(xs - x_span, ys - y_span)
            return mix(
                mix(pos, x_neg, xs, x_min, x_span),
                mix(y_neg, both_neg, xs, x_min, x_span),
                ys,
                y_min,
                y_span
            )
