"""
Function for adding shaped stroke to lines
"""

import itertools
import math
from typing import Callable

import shapely.geometry as g


def sine_stroke(line: g.LineString, max_width: float) -> g.Polygon:
    width = symmetric_stroke_width(
        fn=lambda d: math.sin(d * math.pi / 2) * max_width,
        length=line.length,
    )
    return apply_style(line, width)


def sine_caps_stroke(line: g.LineString, max_width: float, cap_length: float) -> g.Polygon:
    width = capped_stroke_width(
        cap_width=lambda d: math.sin(d * math.pi / 2) * max_width,
        center_width=lambda _: max_width,
        lead_in=cap_length,
        length=line.length,
    )
    return apply_style(line, width)


def triangle_caps_stroke(line: g.LineString, max_width: float, cap_length: float) -> g.Polygon:
    width = capped_stroke_width(
        cap_width=lambda d: d * max_width,
        center_width=lambda _: max_width,
        lead_in=cap_length,
        length=line.length,
    )
    return apply_style(line, width)


def symmetric_stroke_width(fn: Callable[[float], float], length: float) -> Callable[[float], float]:
    def width(d: float) -> float:
        if d < length / 2:
            return fn(d / (length / 2))
        else:
            return fn((length - d) / (length / 2))
    return width


def capped_stroke_width(
    cap_width: Callable[[float], float],
    center_width: Callable[[float], float],
    lead_in: float,
    length: float,
) -> Callable[[float], float]:
    def width(d: float) -> float:
        if d < lead_in:
            return cap_width(d / lead_in)
        elif d > length - lead_in:
            return cap_width((length - d) / lead_in)
        else:
            return center_width((d - lead_in) / (length - (lead_in * 2)))
    return width


def apply_style(line: g.LineString, width: Callable[[float], float]) -> g.Polygon:
    points = [complex(x, y) for x, y in line.coords]
    assert len(points) > 1

    left = 0+1j
    right = 0-1j

    dist = 0
    result = []

    def normalized(c: complex) -> complex:
        return c / abs(c)

    for i in range(len(points)):
        if i != len(points) - 1:
            w = width(dist)
            dist += abs(points[i + 1] - points[i])
        else:
            # Make sure there are no rounding errors on the last point
            w = width(line.length)

        # Find tangent line
        if i == 0:
            tangent = normalized(points[1] - points[0])
        elif i == len(points) - 1:
            tangent = normalized(points[-1] - points[-2])
        else:
            into = normalized(points[i] - points[i - 1])
            outof  = normalized(points[i + 1] - points[i])
            tangent = normalized(into + outof)

        result.append((points[i] + tangent*w/2*right, points[i] + tangent*w/2*left))

    # Remove duplicate points at the far end if they are the same
    if result[-1][0] == result[-1][1]:
        result[-1] = (result[-1][0], None)

    return g.Polygon(
        itertools.chain(
            ((r.real, r.imag) for r, _ in result),
            reversed([(l.real, l.imag) for _, l in result if l is not None]),
        )
    )

