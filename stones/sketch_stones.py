from collections import defaultdict
import math
import random

import numpy as np
import shapely.geometry as s
import sklearn.cluster
import vsketch
from vsketch import Vsketch, Param


def regular_polygon(sides: int) -> s.Polygon:
    angle = 2*math.pi / sides
    r = complex(math.cos(angle), math.sin(angle))
    points = [(0+1j) * r**i for i in range(sides)]
    return s.Polygon((c.real, c.imag) for c in points)


def stones_fill(
    vsk: Vsketch,
    shape: s.Polygon | s.MultiPolygon,
    /,
    density: float,
    max_iterations: int,
    forced_iterations: int,
    recursion_chance: float,
    min_clusters: int,
    max_clusters: int,
    max_fill_chance: float
) -> None:
    (min_x, min_y, max_x, max_y) = shape.bounds
    x = max_x - min_x
    y = max_y - min_y
    points = []
    for _ in range(int(density * x * y)):
        p = s.Point(random.random() * x + min_x, random.random() * y + min_y)
        if shape.intersects(p):
            points.append(p)
    draw_stones(
        vsk,
        points,
        fuel=max_iterations,
        forced_iterations=forced_iterations,
        recursion_chance=recursion_chance,
        min_clusters=min_clusters,
        max_clusters=max_clusters,
        max_fill_chance=max_fill_chance,
    )


def draw_stones(
    vsk: Vsketch,
    points: list[s.Point],
    /,
    fuel: int,
    forced_iterations: int,
    recursion_chance: float,
    min_clusters: int,
    max_clusters: int,
    max_fill_chance: float
) -> None:
    if not fuel or (forced_iterations == 0 and random.random() > recursion_chance):
        hull = s.MultiPoint(points).convex_hull
        if random.random() < max_fill_chance / (fuel+1):
            vsk.fill(2)
            vsk.stroke(2)
        vsk.geometry(hull)
        vsk.noFill()
        vsk.stroke(1)
        return

    # avoid a crash in sklearn
    if not points:
        return

    assert max_clusters >= min_clusters
    max_clusters = min(max_clusters, len(points))
    if max_clusters < min_clusters:
        clusters = max_clusters
    else:
        clusters = random.randint(min_clusters, max_clusters)

    np_points = np.array([[p.x, p.y] for p in points])
    clusters = sklearn.cluster.KMeans(n_clusters=clusters, random_state=random.randrange(2**32)).fit(np_points)

    point_clouds = defaultdict(list)
    for idx, p in zip(clusters.labels_, points):
        point_clouds[idx].append(p)

    for ps in point_clouds.values():
        draw_stones(
            vsk,
            ps,
            fuel=fuel-1,
            forced_iterations=forced_iterations-1,
            recursion_chance=recursion_chance,
            min_clusters=min_clusters,
            max_clusters=max_clusters,
            max_fill_chance=max_fill_chance,
        )


class StonesSketch(vsketch.SketchClass):
    # Sketch parameters:
    max_iterations = Param(4, min_value=1)
    forced_iterations = Param(2, min_value=0)
    recursion_chance = Param(0.4, min_value=0, max_value=1)
    min_clusters = Param(4)
    max_clusters = Param(9)
    density = Param(60.0, min_value=0)
    max_fill_chance = Param(.5, min_value=0, max_value=1)

    shape = Param("polygon", choices=["polygon", "egg", "window", "eye"])
    size = Param(10, min_value=0.001)
    sides = Param(6, min_value=3)


    def validate_params(self) -> bool:
        return self.max_clusters >= self.min_clusters

    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.penWidth("0.15mm")
        vsk.detail("0.01mm")

        if not self.validate_params():
            return

        import shapely.affinity

        # pupil = shapely.affinity.scale(regular_polygon(5), 5, 5)
        eye = s.Point(-self.size, 0).buffer(1.5*self.size).intersection(s.Point(self.size, 0).buffer(1.5*self.size))
        pupil = shapely.affinity.scale(s.Point(0, 0).buffer(1), 0.35*self.size, 0.35*self.size)

        bounds = {
            "polygon": shapely.affinity.scale(regular_polygon(self.sides), self.size, self.size),
            "egg": shapely.affinity.scale(s.Point(0, 0).buffer(1), self.size*0.8, self.size*1.2),
            "window": s.box(-9, -12, 9, 12).difference(shapely.affinity.scale(regular_polygon(self.sides), self.size*.7, self.size*.7)),
            "eye": eye.difference(pupil),
        }

        # points = self.gen_points(bounds[self.shape])
        stones_fill(
            vsk,
            bounds[self.shape],
            density=self.density,
            max_iterations=self.max_iterations,
            forced_iterations=self.forced_iterations,
            recursion_chance=self.recursion_chance,
            min_clusters=self.min_clusters,
            max_clusters=self.max_clusters,
            max_fill_chance=self.max_fill_chance,
        )
        # self.draw_stone(vsk, points, self.max_iterations)

        if self.shape == "eye":
            vsk.fill(3)
            vsk.stroke(3)
            vsk.geometry(pupil.intersection(eye).buffer(-0.06*self.size))
            vsk.noFill()
            vsk.stroke(4)
            vsk.penWidth(".5mm", 4)
            vsk.strokeWeight(4)
            vsk.geometry(eye.buffer(0.12*self.size, join_style=2).union(s.Point(0, 1.24*self.size).buffer(.05*self.size)))
            vsk.stroke(1)

        paper_size = "6inx9in"
        layout = f"layout -h center -v center {paper_size} translate -- 0 -1.5cm"
        pens = "color #004080 penwidth 0.3mm color -l3 black color -l4 gold penwidth -l4 1mm"
        vsk.vpype(f"{layout} {pens}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    StonesSketch.display()
