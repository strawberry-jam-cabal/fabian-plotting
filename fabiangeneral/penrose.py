import dataclasses
from math import (sin, cos, radians, sqrt)


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
        if self.acute:
            ...
        else:
            ...

    def points(self) -> tuple[complex, complex, complex]:
        angle = radians(36) if self.acute else radians(108)
        affine = self.size * complex(cos(self.angle), sin(self.angle))
        return (
            self.origin,
            complex(sin(angle / 2), cos(angle / 2)) * affine + self.origin,
            complex(-sin(angle / 2), cos(angle / 2)) * affine + self.origin,
        )


def dart():
    """Pointing right, oriented at the tail"""
    return (
        GoldenTriangle(0j, angle=radians(36), size=1 / phi, acute=False, join_right=True),
        GoldenTriangle(0j, angle=radians(144), size=1 / phi, acute=False, join_right=False),
    )


def kite():
    """Pointing left, oriented at the nose"""
    return (
        GoldenTriangle(0j, angle=radians(72), size=1, acute=True, join_right=True),
        GoldenTriangle(0j, angle=radians(108), size=1, acute=True, join_right=False),
    )

