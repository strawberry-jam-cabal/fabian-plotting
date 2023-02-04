import dataclasses
from math import (sin, cos, radians, sqrt, pi)


phi = (1 + sqrt(5)) / 2


VERTICES = {
    "ace": p.ace,
    "duce": p.duce,
    "star": p.star,
    "sun": p.sun,
    "jack": p.jack,
    "queen": p.queen,
    "king": p.king,
}


@dataclasses.dataclass(frozen=True, slots=True)
class GoldenTriangle:
    origin: complex
    angle: float
    size: float
    acute: bool
    join_right: bool

    def scale(self, factor: float) -> "GoldenTriangle":
        return dataclasses.replace(self, size=self.size + factor)

    def rotate(self, angle: float) -> "GoldenTriangle":
        return dataclasses.replace(self, angle=self.angle + angle)

    def translate(self, vec: complex) -> "GoldenTriangle":
        return dataclasses.replace(self, origin=self.origin + vec)

    def decompose(self) -> list["GoldenTriangle"]:
        factor = 1 / phi
        vertices = self.points()
        result = []

        if self.acute:
            kite_origin = vertices[1]
            kite_angle = radians(36) if self.join_right else radians(144)
            result.extend(kite(origin=kite_origin, angle=(self.angle + kite_angle) % (2*pi), size=self.size * factor))

            tri_origin = self.origin + (kite_origin - self.origin) * (1-factor)
            tri_angle = radians(108) if self.join_right else radians(-108)
            result.append(GoldenTriangle(origin=tri_origin, angle=(self.angle + tri_angle) % (2*pi), size=self.size * factor / phi, acute=False, join_right=self.join_right))
        else:
            a_origin = vertices[2]
            a_angle = radians(-108) if self.join_right else radians(108)
            a = GoldenTriangle(origin=a_origin, angle=(self.angle + a_angle) % (2*pi), size=self.size, acute=True, join_right=not self.join_right)
            result.append(a)

            a_vertices = a.points()
            o_origin = a_vertices[1]
            o_angle = radians(-144) if self.join_right else radians(144)
            result.append(GoldenTriangle(o_origin, (self.angle + o_angle) % (2*pi), size=self.size * factor, acute=False, join_right=self.join_right))

        return result

    def points(self) -> tuple[complex, complex, complex]:
        angle = radians(36) if self.acute else radians(108)
        affine = self.size * complex(cos(self.angle), sin(self.angle))
        bottom = [
            complex(sin(angle / 2), cos(angle / 2)) * affine + self.origin,
            complex(-sin(angle / 2), cos(angle / 2)) * affine + self.origin,
        ]
        if not self.join_right:
            bottom.reverse()
        return [self.origin] + bottom

    def arcs(self) -> list[tuple[complex, complex, float]]:
        """Nose arc and tail arc, represented as (origin, radial vector, angle)"""
        vertices = self.points()
        direction = 1 if self.join_right else -1
        if self.acute:
            nose_center = self.origin
            tail_center = vertices[2]
            nose_vector = (tail_center - nose_center) / phi
            tail_vector = (nose_center - tail_center) + nose_vector
            nose_angle = direction * radians(-36)
            tail_angle = direction * radians(72)
        else:
            nose_center = vertices[2]
            nose_vector = (vertices[1] - nose_center) * (1 - 1/phi)
            nose_angle = direction * radians(-36)
            tail_center = self.origin
            nose_end = nose_vector * complex(cos(nose_angle), sin(nose_angle))
            tail_vector = (nose_center - tail_center) + nose_end
            tail_angle = direction * radians(-108)
        return [
            (nose_center, nose_vector, nose_angle),
            (tail_center, tail_vector, tail_angle),
        ]


def dart(origin: complex = 0j, angle: float = 0, size: float = 1) -> list[GoldenTriangle]:
    """Pointing right, oriented at the tail"""
    return [
        GoldenTriangle(origin, angle=angle + radians(36), size=size / phi, acute=False, join_right=True),
        GoldenTriangle(origin, angle=angle + radians(144), size=size / phi, acute=False, join_right=False),
    ]


def kite(origin: complex = 0j, angle: float = 0, size: float = 1) -> list[GoldenTriangle]:
    """Pointing left, oriented at the nose"""
    return [
        GoldenTriangle(origin, angle=angle + radians(72), size=size, acute=True, join_right=True),
        GoldenTriangle(origin, angle=angle + radians(108), size=size, acute=True, join_right=False),
    ]


def sun(origin: complex = 0j, angle: float = 0, size: float = 1) -> list[GoldenTriangle]:
    return [
        t
        for a in range(0, 360, 72)
        for t in kite(origin=origin, angle=angle + radians(a), size=size)
    ]


def star(origin: complex = 0j, angle: float = 0, size: float = 1) -> list[GoldenTriangle]:
    offset = complex(size / phi, 0) * complex(cos(angle), sin(angle))
    step = complex(cos(radians(72)), sin(radians(72)))
    return [
        t
        for i in range(5)
        for t in dart(origin=origin + (offset * step**i), angle=angle + radians(72*i), size=size)
    ]


def ace(origin: complex = 0j, angle: float = 0, size: float = 1) -> list[GoldenTriangle]:
    rotation = complex(cos(angle), sin(angle))
    to_kites = complex(0, size) * rotation
    tiles = [
        dart(origin=origin, angle=angle + radians(90), size=size),
        kite(origin=origin + to_kites, angle=angle + radians(54), size=size),
        kite(origin=origin + to_kites, angle=angle + radians(126), size=size),
    ]
    return [
        tri
        for t in tiles
        for tri in t
    ]


def duce(origin: complex = 0j, angle: float = 0, size: float = 1) -> list[GoldenTriangle]:
    def rotation(a): return complex(cos(a), sin(a))
    to_kite = complex(0, -size) * rotation(angle)
    to_dart = complex(0, -size / phi) * rotation(angle)
    tiles = [
        dart(origin=origin + to_dart * rotation(radians(-36)), angle=angle + radians(90+36), size=size),
        dart(origin=origin + to_dart * rotation(radians(36)), angle=angle + radians(90-36), size=size),
        kite(origin=origin + to_kite * rotation(radians(-108)), angle=angle + radians(162), size=size),
        kite(origin=origin + to_kite * rotation(radians(108)), angle=angle + radians(18), size=size),
    ]
    return [
        tri
        for t in tiles
        for tri in t
    ]


def king(origin: complex = 0j, angle: float = 0, size: float = 1) -> list[GoldenTriangle]:
    def rotation(a): return complex(cos(a), sin(a))
    to_kite = complex(0, -size) * rotation(angle)
    to_dart = complex(0, -size / phi) * rotation(angle)
    tiles = [
        dart(origin=origin + to_dart * rotation(radians(0)), angle=angle + radians(-90), size=size),
        dart(origin=origin + to_dart * rotation(radians(-72)), angle=angle + radians(-162), size=size),
        dart(origin=origin + to_dart * rotation(radians(72)), angle=angle + radians(-18), size=size),
        kite(origin=origin + to_kite * rotation(radians(-108)), angle=angle + radians(-162), size=size),
        kite(origin=origin + to_kite * rotation(radians(108)), angle=angle + radians(-18), size=size),
    ]
    return [
        tri
        for t in tiles
        for tri in t
    ]


def queen(origin: complex = 0j, angle: float = 0, size: float = 1) -> list[GoldenTriangle]:
    def rotation(a): return complex(cos(a), sin(a))
    to_kite = complex(0, -size) * rotation(angle)
    to_dart = complex(0, -size / phi) * rotation(angle)
    tiles = [
        dart(origin=origin + to_dart * rotation(radians(0)), angle=angle + radians(-90), size=size),
        kite(origin=origin + to_kite * rotation(radians(-36)), angle=angle + radians(-90), size=size),
        kite(origin=origin + to_kite * rotation(radians(36)), angle=angle + radians(-90), size=size),
        kite(origin=origin + to_kite * rotation(radians(180)), angle=angle + radians(54), size=size),
        kite(origin=origin + to_kite * rotation(radians(180)), angle=angle + radians(126), size=size),
    ]
    return [
        tri
        for t in tiles
        for tri in t
    ]


def jack(origin: complex = 0j, angle: float = 0, size: float = 1) -> list[GoldenTriangle]:
    def rotation(a): return complex(cos(a), sin(a))
    to_kite = complex(0, -size) * rotation(angle)
    to_dart = complex(0, -size / phi) * rotation(angle)
    tiles = [
        kite(origin=origin + to_kite, angle=angle + radians(-90), size=size),
        dart(origin=origin + to_dart * rotation(radians(-72)), angle=angle + radians(-54), size=size),
        dart(origin=origin + to_dart * rotation(radians(72)), angle=angle + radians(-126), size=size),
        kite(origin=origin, angle=angle + radians(-54), size=size),
        kite(origin=origin, angle=angle + radians(-126), size=size),
    ]
    return [
        tri
        for t in tiles
        for tri in t
    ]
