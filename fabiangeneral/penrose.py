import dataclasses
from math import (sin, cos, radians, sqrt, pi)


phi = (1 + sqrt(5)) / 2


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
            kite_origin = vertices[1] if self.join_right else vertices[2]
            kite_angle = radians(36) if self.join_right else radians(144)
            result.extend(kite(origin=kite_origin, angle=(self.angle + kite_angle) % (2*pi), size=self.size * factor))

            tri_origin = self.origin + (kite_origin - self.origin) * (1-factor)
            tri_angle = radians(108) if self.join_right else radians(-108)
            result.append(GoldenTriangle(origin=tri_origin, angle=(self.angle + tri_angle) % (2*pi), size=self.size * factor / phi, acute=False, join_right=self.join_right))
        else:
            a_origin = vertices[1] if self.join_right else vertices[2]
            a_angle = radians(108) if self.join_right else radians(-108)
            a = GoldenTriangle(origin=a_origin, angle=(self.angle + a_angle) % (2*pi), size=self.size, acute=True, join_right=not self.join_right)
            result.append(a)

            a_vertices = a.points()
            o_origin = a_vertices[1] if self.join_right else a_vertices[2]
            o_angle = radians(144) if self.join_right else radians(-144)
            result.append(GoldenTriangle(o_origin, (self.angle + o_angle) % (2*pi), size=self.size * factor, acute=False, join_right=self.join_right))

        return result

    def points(self) -> tuple[complex, complex, complex]:
        angle = radians(36) if self.acute else radians(108)
        affine = self.size * complex(cos(self.angle), sin(self.angle))
        return (
            self.origin,
            complex(sin(angle / 2), cos(angle / 2)) * affine + self.origin,
            complex(-sin(angle / 2), cos(angle / 2)) * affine + self.origin,
        )


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
