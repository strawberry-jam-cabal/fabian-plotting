import vsketch
from vsketch import Param, Vsketch


class TextSketch(vsketch.SketchClass):
    page_size = Param("4inx5.5in", choices=["11inx15in", "8.5inx11in", "6inx9in", "6inx8in", "4.5inx6.25in", "4inx5.5in", "2.5inx3.75in"])
    landscape = Param(False)
    pen_width = Param(0.25)
    x = Param(0.5)
    y = Param(0.6)
    width = Param(600)
    size = Param(12)
    font = Param(
        "astrology",
        choices=[
            "astrology",
            "cursive",
            "futural",
            "greeks",
            "gothgbt",
            "mathupp",
            "gothicger",
            "scriptc",
            "greekc",
            "greek",
            "rowmant",
            "futuram",
            "cyrillic",
            "gothitt",
            "meteorology",
            "gothicita",
            "scripts",
            "timesg",
            "cyrilc_1",
            "gothiceng",
            "timesr",
            "rowmand",
            "markers",
            "timesrb",
            "music",
            "rowmans",
            "japanese",
            "mathlow",
            "timesi",
            "symbolic",
            "timesib",
            "gothgrt",
        ]
    )
    text = Param("Hello world")

    def draw(self, vsk: Vsketch) -> None:
        vsk.centered = False
        vsk.penWidth(f"{self.pen_width}mm")
        layout = f"layout {'-l'if self.landscape else ''} {self.page_size}"
        pen = f"penwidth {self.pen_width}mm color black"
        vsk.vpype(f"{layout} {pen}")
        vsk.text(self.text, self.x, self.y, width=self.width, font=self.font, size=self.size)

    def finalize(self, vsk: Vsketch) -> None:
        vsk.vpype("")


if __name__ == "__main__":
    TextSketch.display()
