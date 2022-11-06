import vsketch
from vsketch import Param, Vsketch


class TestSketch(vsketch.SketchClass):
    page_size = Param("6inx9in", choices=["8.5inx11in", "6inx9in", "4.5inx6.25in", "2.5inx3.75in"])
    pen_width = Param(0.45)
    scale = Param(1.0)

    start = Param(0.02)
    stop = Param(0.06)
    step = Param(0.005)

    def draw(self, vsk: Vsketch) -> None:
        vsk.scale("cm")
        vsk.centered = False

        # implement your sketch here
        y = 0
        x = 0
        space = self.start
        while space < self.stop + 0.001:
            x = 0
            y -= self.scale/2
            vsk.line(x-space, y, x-space, y+self.scale)
            vsk.line(x, y, x, y+self.scale)
            vsk.line(x+space, y, x+space, y+self.scale)
            y += self.scale/2
            x += self.scale
            vsk.line(x, y-space, x+self.scale, y-space)
            vsk.line(x, y, x+self.scale, y)
            vsk.line(x, y+space, x+self.scale, y+space)
            x += self.scale*2.5
            vsk.circle(x, y, diameter=self.scale, mode="center")
            vsk.circle(x, y, diameter=self.scale-space*2, mode="center")
            x += self.scale*2
            vsk.square(x, y, self.scale, mode="center")
            vsk.square(x, y, self.scale-space*2, mode="center")

            x += self.scale*2
            vsk.penWidth(f"{space}cm")
            vsk.strokeWeight(3)
            vsk.square(x, y, self.scale, mode="center")
            vsk.strokeWeight(1)

            x += self.scale*2
            vsk.fill(1)
            vsk.square(x, y, self.scale, mode="center")
            vsk.noFill()

            y += 2*self.scale
            space += self.step

        layout = f"layout {self.page_size}"
        pen = f"penwidth {self.pen_width}mm color black"
        vsk.vpype(f"{layout} {pen}")

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("linesort --two-opt linesimplify -t0.01mm")


if __name__ == "__main__":
    TestSketch.display()
